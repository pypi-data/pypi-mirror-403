"""Hidden Markov Model for haplotype state inference.

This module implements HMM-based haplotype inference for smoother,
more accurate ancestry calls along chromosomes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from itertools import combinations_with_replacement
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet
    from haplophaser.proportion.genotypes import SampleMarkerGenotypes

logger = logging.getLogger(__name__)


@dataclass
class HMMResult:
    """Results from HMM inference for a single sample on one chromosome.

    Attributes:
        sample: Sample name
        chrom: Chromosome name
        markers: List of marker IDs in order
        positions: Genomic positions of markers
        states: List of possible state names
        viterbi_path: Most likely state at each marker position
        posteriors: Posterior probabilities, shape (n_markers, n_states)
        smoothed_proportions: Per-position founder probabilities
        log_likelihood: Log-likelihood of the observations
    """

    sample: str
    chrom: str
    markers: list[str]
    positions: list[int]
    states: list[str]
    viterbi_path: list[str]
    posteriors: np.ndarray
    smoothed_proportions: list[dict[str, float]]
    log_likelihood: float = 0.0
    founders: list[str] = field(default_factory=list)
    # Alias for backwards compatibility
    sample_name: str = field(init=False, default="")

    def __post_init__(self) -> None:
        """Set sample_name alias."""
        self.sample_name = self.sample

    @property
    def n_markers(self) -> int:
        """Get number of markers."""
        return len(self.markers)

    @property
    def n_states(self) -> int:
        """Get number of states."""
        return len(self.states)

    def get_state_at(self, pos: int) -> str | None:
        """Get Viterbi state at or near a position.

        Args:
            pos: Genomic position

        Returns:
            State name or None if no markers nearby
        """
        if not self.positions:
            return None

        # Find nearest marker
        idx = np.searchsorted(self.positions, pos)
        if idx >= len(self.positions):
            idx = len(self.positions) - 1
        elif idx > 0:
            # Check which is closer
            if abs(self.positions[idx] - pos) > abs(self.positions[idx - 1] - pos):
                idx = idx - 1

        return self.viterbi_path[idx]

    def get_posterior_at(self, pos: int) -> dict[str, float]:
        """Get posterior probabilities at or near a position.

        Returns founder-level proportions (not raw state posteriors).

        Args:
            pos: Genomic position

        Returns:
            Dict mapping founder names to probabilities
        """
        if not self.positions:
            return {}

        # Find nearest marker
        idx = np.searchsorted(self.positions, pos)
        if idx >= len(self.positions):
            idx = len(self.positions) - 1
        elif idx > 0:
            if abs(self.positions[idx] - pos) > abs(self.positions[idx - 1] - pos):
                idx = idx - 1

        # Return smoothed proportions (founder-level) if available
        if self.smoothed_proportions and idx < len(self.smoothed_proportions):
            return self.smoothed_proportions[idx]

        # Otherwise return raw state posteriors
        return {s: float(self.posteriors[idx, i]) for i, s in enumerate(self.states)}

    def get_viterbi_segments(self) -> list[dict]:
        """Get Viterbi path as contiguous segments.

        Returns:
            List of dicts with keys: 'start', 'end', 'state', 'n_markers'
        """
        if not self.viterbi_path or not self.positions:
            return []

        segments = []
        current_state = self.viterbi_path[0]
        seg_start = self.positions[0]
        seg_start_idx = 0

        for i in range(1, len(self.viterbi_path)):
            if self.viterbi_path[i] != current_state:
                # End current segment
                segments.append({
                    "start": seg_start,
                    "end": self.positions[i - 1],
                    "state": current_state,
                    "n_markers": i - seg_start_idx,
                })
                # Start new segment
                current_state = self.viterbi_path[i]
                seg_start = self.positions[i]
                seg_start_idx = i

        # Add final segment
        segments.append({
            "start": seg_start,
            "end": self.positions[-1],
            "state": current_state,
            "n_markers": len(self.viterbi_path) - seg_start_idx,
        })

        return segments

    def to_blocks(self, min_markers: int = 1) -> list:
        """Convert Viterbi path to haplotype blocks.

        Args:
            min_markers: Minimum markers to form a block

        Returns:
            List of HaplotypeBlock objects
        """
        from haplophaser.proportion.blocks import HaplotypeBlock

        if not self.viterbi_path:
            return []

        blocks = []
        current_state = self.viterbi_path[0]
        block_start = self.positions[0]
        block_markers = 1
        block_posteriors = [self.posteriors[0]]

        for i in range(1, len(self.viterbi_path)):
            if self.viterbi_path[i] != current_state:
                # End current block
                if block_markers >= min_markers:
                    mean_posterior = np.mean([p[self.states.index(current_state)]
                                              for p in block_posteriors])
                    blocks.append(HaplotypeBlock(
                        chrom=self.chrom,
                        start=block_start,
                        end=self.positions[i - 1] + 1,
                        dominant_founder=current_state,
                        mean_proportion=float(mean_posterior),
                        min_proportion=float(min(p[self.states.index(current_state)]
                                                  for p in block_posteriors)),
                        max_proportion=float(max(p[self.states.index(current_state)]
                                                  for p in block_posteriors)),
                        n_windows=block_markers,
                        confidence=float(mean_posterior),
                    ))

                # Start new block
                current_state = self.viterbi_path[i]
                block_start = self.positions[i]
                block_markers = 1
                block_posteriors = [self.posteriors[i]]
            else:
                block_markers += 1
                block_posteriors.append(self.posteriors[i])

        # Close final block
        if block_markers >= min_markers:
            mean_posterior = np.mean([p[self.states.index(current_state)]
                                      for p in block_posteriors])
            blocks.append(HaplotypeBlock(
                chrom=self.chrom,
                start=block_start,
                end=self.positions[-1] + 1,
                dominant_founder=current_state,
                mean_proportion=float(mean_posterior),
                min_proportion=float(min(p[self.states.index(current_state)]
                                          for p in block_posteriors)),
                max_proportion=float(max(p[self.states.index(current_state)]
                                          for p in block_posteriors)),
                n_windows=block_markers,
                confidence=float(mean_posterior),
            ))

        return blocks

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sample": self.sample,
            "chrom": self.chrom,
            "markers": self.markers,
            "positions": self.positions,
            "states": self.states,
            "viterbi_path": self.viterbi_path,
            "posteriors": self.posteriors.tolist(),
            "smoothed_proportions": self.smoothed_proportions,
            "log_likelihood": self.log_likelihood,
        }


@dataclass
class HMMResults:
    """Collection of HMM results for multiple samples and chromosomes.

    Attributes:
        results: Dict mapping (sample, chrom) to HMMResult
        founders: List of founder names
        states: List of state names
        ploidy: Sample ploidy
    """

    results: dict[tuple[str, str], HMMResult] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    ploidy: int = 2

    def add_result(self, result: HMMResult) -> None:
        """Add a result for a sample/chromosome."""
        self.results[(result.sample, result.chrom)] = result

    def get_result(self, sample: str, chrom: str) -> HMMResult | None:
        """Get result for a specific sample and chromosome."""
        return self.results.get((sample, chrom))

    def get_sample_results(self, sample: str) -> list[HMMResult]:
        """Get all results for a sample."""
        return [r for (s, c), r in self.results.items() if s == sample]

    def get_chromosome_results(self, chrom: str) -> list[HMMResult]:
        """Get all results for a chromosome."""
        return [r for (s, c), r in self.results.items() if c == chrom]

    @property
    def samples(self) -> list[str]:
        """Get list of samples."""
        return list({s for s, c in self.results})

    @property
    def chromosomes(self) -> list[str]:
        """Get list of chromosomes."""
        return list({c for s, c in self.results})

    @property
    def n_samples(self) -> int:
        """Get number of unique samples."""
        return len(self.samples)

    @property
    def n_results(self) -> int:
        """Get total number of results (sample × chromosome combinations)."""
        return len(self.results)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "founders": self.founders,
            "states": self.states,
            "ploidy": self.ploidy,
            "results": {
                f"{s}:{c}": r.to_dict() for (s, c), r in self.results.items()
            },
        }


class HaplotypeHMM:
    """Hidden Markov Model for haplotype state inference.

    Models haplotype inheritance along chromosomes with states
    representing different founder combinations.
    """

    def __init__(
        self,
        founders: list[str],
        ploidy: int = 2,
        recombination_rate: float = 1e-8,
        genotyping_error: float = 0.01,
        genetic_map: GeneticMap | None = None,
    ) -> None:
        """Initialize the HMM.

        Args:
            founders: List of founder names
            ploidy: Sample ploidy (default 2)
            recombination_rate: Per-bp recombination rate (used if no genetic map)
            genotyping_error: Genotyping error rate for emission probabilities
            genetic_map: Optional genetic map for accurate recombination modeling
        """
        self.founders = founders
        self.ploidy = ploidy
        self.recombination_rate = recombination_rate
        self.genotyping_error = genotyping_error
        self.genetic_map = genetic_map

        # Generate states based on ploidy and founders
        self.states = self._generate_states()
        self.n_states = len(self.states)
        self.state_to_idx = {s: i for i, s in enumerate(self.states)}

        logger.debug(f"HMM initialized with {self.n_states} states: {self.states}")

    @property
    def _transition_matrix(self) -> np.ndarray:
        """Get default transition matrix (single step).

        Returns a transition matrix with default recombination probability.
        Useful for testing and inspection.

        Returns:
            Array of shape (n_states, n_states)
        """
        # Use default recombination probability (e.g., for ~1000bp distance)
        recomb_prob = min(0.5, self.recombination_rate * 1000)
        p_stay = 1 - recomb_prob

        trans = np.zeros((self.n_states, self.n_states))
        for i in range(self.n_states):
            for j in range(self.n_states):
                if i == j:
                    trans[i, j] = p_stay
                else:
                    trans[i, j] = recomb_prob / (self.n_states - 1) if self.n_states > 1 else 0
        return trans

    def _generate_states(self) -> list[str]:
        """Generate HMM states based on ploidy and founders.

        For diploids: states are founder combinations (AA, AB, BB, etc.)
        For polyploids: states represent dosage combinations.

        Returns:
            List of state names
        """
        if self.ploidy == 2:
            # Diploid: unordered pairs
            states = []
            for combo in combinations_with_replacement(self.founders, 2):
                states.append("/".join(combo))
            return states
        else:
            # Polyploid: combinations with replacement
            states = []
            for combo in combinations_with_replacement(self.founders, self.ploidy):
                states.append("/".join(combo))
            return states

    def _get_state_founder_dosage(self, state: str) -> dict[str, int]:
        """Get founder dosages for a state.

        Args:
            state: State name (e.g., "B73/Mo17")

        Returns:
            Dict mapping founder names to dosage counts
        """
        parts = state.split("/")
        dosage = dict.fromkeys(self.founders, 0)
        for p in parts:
            if p in dosage:
                dosage[p] += 1
        return dosage

    def _compute_transition_matrix(
        self,
        positions: list[int],
        chrom: str,
    ) -> np.ndarray:
        """Compute transition probability matrices between positions.

        Args:
            positions: List of marker positions
            chrom: Chromosome name

        Returns:
            Array of shape (n_positions-1, n_states, n_states)
        """
        n_positions = len(positions)
        transitions = np.zeros((n_positions - 1, self.n_states, self.n_states))

        for i in range(n_positions - 1):
            pos1, pos2 = positions[i], positions[i + 1]

            # Get recombination probability
            if self.genetic_map is not None:
                recomb_prob = self.genetic_map.recombination_probability(chrom, pos1, pos2)
            else:
                # Use per-bp rate
                distance = abs(pos2 - pos1)
                recomb_prob = min(0.5, self.recombination_rate * distance)

            # Build transition matrix
            # Probability of staying in same state
            p_stay = 1 - recomb_prob

            for j in range(self.n_states):
                for k in range(self.n_states):
                    if j == k:
                        transitions[i, j, k] = p_stay
                    else:
                        # Probability of transitioning to a different state
                        # Distribute equally among all other states
                        transitions[i, j, k] = recomb_prob / (self.n_states - 1)

        return transitions

    def _compute_emission_probs(
        self,
        genotype,
        marker,
    ) -> np.ndarray:
        """Compute emission probabilities for an observed genotype.

        P(observed_alleles | haplotype_state, marker_frequencies)

        Args:
            genotype: Observed MarkerGenotype
            marker: DiagnosticMarker with founder frequencies

        Returns:
            Array of shape (n_states,) with emission probabilities
        """
        emissions = np.zeros(self.n_states)

        if genotype.is_missing:
            # Missing data: uniform emission
            emissions[:] = 1.0 / self.n_states
            return emissions

        # Get observed allele frequencies
        genotype.get_allele_frequency(marker.ref)
        genotype.get_allele_frequency(marker.alt)

        for i, state in enumerate(self.states):
            # Get founder dosages for this state
            dosages = self._get_state_founder_dosage(state)

            # Expected allele frequency given this state
            exp_ref = 0.0
            exp_alt = 0.0
            total_dosage = sum(dosages.values())

            for founder, dosage in dosages.items():
                if dosage == 0:
                    continue
                founder_freqs = marker.founder_frequencies.get(founder, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                exp_ref += (dosage / total_dosage) * founder_ref
                exp_alt += (dosage / total_dosage) * founder_alt

            # Emission probability: how well does observation match expectation?
            # Use a simple model based on allele frequency match
            # Account for genotyping error
            error = self.genotyping_error

            # For each observed allele, probability of seeing it given state
            prob = 1.0
            for allele in genotype.alleles:
                if allele == marker.ref:
                    p_allele = exp_ref * (1 - error) + exp_alt * error
                elif allele == marker.alt:
                    p_allele = exp_alt * (1 - error) + exp_ref * error
                else:
                    p_allele = error  # Unknown allele

                prob *= max(p_allele, 1e-10)

            emissions[i] = prob

        # Normalize
        total = emissions.sum()
        if total > 0:
            emissions /= total
        else:
            emissions[:] = 1.0 / self.n_states

        return emissions

    def _forward_algorithm(
        self,
        emissions: np.ndarray,
        transitions: np.ndarray,
        initial: np.ndarray,
    ) -> tuple[np.ndarray, float]:
        """Run forward algorithm.

        Args:
            emissions: Emission probabilities, shape (T, n_states)
            transitions: Transition matrices, shape (T-1, n_states, n_states)
            initial: Initial state probabilities, shape (n_states,)

        Returns:
            Tuple of (forward probabilities, log-likelihood)
        """
        T = emissions.shape[0]
        alpha = np.zeros((T, self.n_states))
        scale = np.zeros(T)

        # Initialize
        alpha[0] = initial * emissions[0]
        scale[0] = alpha[0].sum()
        if scale[0] > 0:
            alpha[0] /= scale[0]

        # Forward pass
        for t in range(1, T):
            for j in range(self.n_states):
                alpha[t, j] = emissions[t, j] * np.sum(
                    alpha[t - 1] * transitions[t - 1, :, j]
                )
            scale[t] = alpha[t].sum()
            if scale[t] > 0:
                alpha[t] /= scale[t]

        # Log-likelihood
        log_likelihood = np.sum(np.log(scale[scale > 0]))

        return alpha, log_likelihood

    def _backward_algorithm(
        self,
        emissions: np.ndarray,
        transitions: np.ndarray,
        scale: np.ndarray,
    ) -> np.ndarray:
        """Run backward algorithm.

        Args:
            emissions: Emission probabilities, shape (T, n_states)
            transitions: Transition matrices, shape (T-1, n_states, n_states)
            scale: Scaling factors from forward algorithm

        Returns:
            Backward probabilities, shape (T, n_states)
        """
        T = emissions.shape[0]
        beta = np.zeros((T, self.n_states))

        # Initialize
        beta[T - 1] = 1.0

        # Backward pass
        for t in range(T - 2, -1, -1):
            for i in range(self.n_states):
                beta[t, i] = np.sum(
                    transitions[t, i, :] * emissions[t + 1] * beta[t + 1]
                )
            if scale[t + 1] > 0:
                beta[t] /= scale[t + 1]

        return beta

    def _viterbi_algorithm(
        self,
        emissions: np.ndarray,
        transitions: np.ndarray,
        initial: np.ndarray,
    ) -> list[int]:
        """Run Viterbi algorithm to find most likely state sequence.

        Args:
            emissions: Emission probabilities, shape (T, n_states)
            transitions: Transition matrices, shape (T-1, n_states, n_states)
            initial: Initial state probabilities, shape (n_states,)

        Returns:
            List of most likely state indices
        """
        T = emissions.shape[0]

        # Use log probabilities to avoid underflow
        log_emissions = np.log(np.maximum(emissions, 1e-300))
        log_transitions = np.log(np.maximum(transitions, 1e-300))
        log_initial = np.log(np.maximum(initial, 1e-300))

        # Viterbi variables
        delta = np.zeros((T, self.n_states))
        psi = np.zeros((T, self.n_states), dtype=int)

        # Initialize
        delta[0] = log_initial + log_emissions[0]

        # Forward pass
        for t in range(1, T):
            for j in range(self.n_states):
                scores = delta[t - 1] + log_transitions[t - 1, :, j]
                psi[t, j] = np.argmax(scores)
                delta[t, j] = scores[psi[t, j]] + log_emissions[t, j]

        # Backtrack
        path = [0] * T
        path[T - 1] = np.argmax(delta[T - 1])

        for t in range(T - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]

        return path

    def fit_predict(
        self,
        marker_genotypes: dict[str, SampleMarkerGenotypes],
        diagnostic_markers: DiagnosticMarkerSet,
        samples: list[str] | None = None,
    ) -> HMMResults:
        """Fit HMM and predict haplotype states for all samples.

        Args:
            marker_genotypes: Dict mapping sample names to their marker genotypes
            diagnostic_markers: Set of diagnostic markers
            samples: Optional list of samples to process (default: all)

        Returns:
            HMMResults with Viterbi paths and posteriors
        """
        logger.info(f"Running HMM inference for {len(marker_genotypes)} samples")

        if samples is None:
            samples = list(marker_genotypes.keys())

        results = HMMResults(
            founders=self.founders,
            states=self.states,
            ploidy=self.ploidy,
        )

        # Build marker lookup
        marker_by_id = {m.variant_id: m for m in diagnostic_markers}

        for sample in samples:
            genotypes = marker_genotypes.get(sample)
            if genotypes is None:
                continue

            # Process each chromosome
            for chrom in genotypes.get_chromosomes():
                chrom_result = self._process_chromosome(
                    sample, chrom, genotypes, marker_by_id
                )
                if chrom_result is not None:
                    results.add_result(chrom_result)

        logger.info(f"HMM inference complete: {len(results.results)} chromosome results")
        return results

    def _process_chromosome(
        self,
        sample: str,
        chrom: str,
        genotypes: SampleMarkerGenotypes,
        marker_by_id: dict,
    ) -> HMMResult | None:
        """Process a single chromosome for a sample.

        Args:
            sample: Sample name
            chrom: Chromosome name
            genotypes: Sample's marker genotypes
            marker_by_id: Dict mapping marker IDs to DiagnosticMarker objects

        Returns:
            HMMResult for this chromosome or None if insufficient data
        """
        # Get genotypes for this chromosome
        chrom_genos = genotypes.get_chromosome_genotypes(chrom)
        if len(chrom_genos) < 2:
            logger.debug(f"Skipping {sample}:{chrom} - insufficient markers")
            return None

        # Filter to genotypes with marker info
        valid_genos = []
        valid_markers = []
        for geno in chrom_genos:
            marker = marker_by_id.get(geno.variant_id)
            if marker is not None:
                valid_genos.append(geno)
                valid_markers.append(marker)

        if len(valid_genos) < 2:
            return None

        # Sort by position
        sorted_data = sorted(zip(valid_genos, valid_markers, strict=False), key=lambda x: x[0].pos)
        valid_genos = [g for g, m in sorted_data]
        valid_markers = [m for g, m in sorted_data]

        positions = [g.pos for g in valid_genos]
        marker_ids = [g.variant_id for g in valid_genos]

        # Compute emissions
        n_markers = len(valid_genos)
        emissions = np.zeros((n_markers, self.n_states))

        for i, (geno, marker) in enumerate(zip(valid_genos, valid_markers, strict=False)):
            emissions[i] = self._compute_emission_probs(geno, marker)

        # Compute transitions
        transitions = self._compute_transition_matrix(positions, chrom)

        # Initial state probabilities (uniform)
        initial = np.ones(self.n_states) / self.n_states

        # Forward-backward for posteriors
        alpha, log_likelihood = self._forward_algorithm(emissions, transitions, initial)

        # Get scale factors for backward
        scale = alpha.sum(axis=1)
        scale[scale == 0] = 1.0

        beta = self._backward_algorithm(emissions, transitions, scale)

        # Compute posteriors
        posteriors = alpha * beta
        row_sums = posteriors.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        posteriors /= row_sums

        # Viterbi for most likely path
        viterbi_indices = self._viterbi_algorithm(emissions, transitions, initial)
        viterbi_path = [self.states[i] for i in viterbi_indices]

        # Compute smoothed proportions from posteriors
        smoothed_proportions = []
        for i in range(n_markers):
            founder_probs = dict.fromkeys(self.founders, 0.0)
            for j, state in enumerate(self.states):
                dosages = self._get_state_founder_dosage(state)
                total_dosage = sum(dosages.values())
                for founder, dosage in dosages.items():
                    founder_probs[founder] += posteriors[i, j] * (dosage / total_dosage)
            smoothed_proportions.append(founder_probs)

        return HMMResult(
            sample=sample,
            chrom=chrom,
            markers=marker_ids,
            positions=positions,
            states=self.states,
            viterbi_path=viterbi_path,
            posteriors=posteriors,
            smoothed_proportions=smoothed_proportions,
            log_likelihood=log_likelihood,
        )

    def predict_single(
        self,
        genotypes: SampleMarkerGenotypes,
        diagnostic_markers: DiagnosticMarkerSet,
        chrom: str,
    ) -> HMMResult | None:
        """Predict haplotype states for a single sample and chromosome.

        Args:
            genotypes: Sample's marker genotypes
            diagnostic_markers: Set of diagnostic markers
            chrom: Chromosome to process

        Returns:
            HMMResult or None if insufficient data
        """
        marker_by_id = {m.variant_id: m for m in diagnostic_markers}
        return self._process_chromosome(
            genotypes.sample_name, chrom, genotypes, marker_by_id
        )

    def baum_welch(
        self,
        marker_genotypes: dict[str, SampleMarkerGenotypes],
        diagnostic_markers: DiagnosticMarkerSet,
        max_iterations: int = 100,
        convergence_threshold: float = 1e-4,
        samples: list[str] | None = None,
    ) -> dict:
        """Learn optimal HMM parameters using Baum-Welch (EM) algorithm.

        This method iteratively updates the transition probabilities and
        genotyping error rate to maximize the likelihood of the observed data.

        Args:
            marker_genotypes: Dict mapping sample names to their marker genotypes
            diagnostic_markers: Set of diagnostic markers
            max_iterations: Maximum EM iterations
            convergence_threshold: Stop when log-likelihood change < threshold
            samples: Optional list of samples to use for training

        Returns:
            Dict with learned parameters and convergence info:
            - 'recombination_rate': Learned recombination rate
            - 'genotyping_error': Learned error rate
            - 'log_likelihoods': List of log-likelihoods per iteration
            - 'converged': Whether algorithm converged
            - 'n_iterations': Number of iterations run
        """
        logger.info("Running Baum-Welch parameter estimation")

        if samples is None:
            samples = list(marker_genotypes.keys())

        # Build marker lookup
        marker_by_id = {m.variant_id: m for m in diagnostic_markers}

        # Get all chromosomes and prepare data
        all_data = []  # List of (emissions, positions, chrom) tuples
        for sample_name in samples:
            genos = marker_genotypes[sample_name]
            for chrom in genos.get_chromosomes():
                chrom_genos = list(genos.get_chromosome_genotypes(chrom))
                valid_genos = []
                valid_markers = []
                for g in sorted(chrom_genos, key=lambda x: x.pos):
                    if g.variant_id in marker_by_id and not g.is_missing:
                        valid_genos.append(g)
                        valid_markers.append(marker_by_id[g.variant_id])

                if len(valid_genos) >= 2:
                    positions = [g.pos for g in valid_genos]
                    emissions = np.zeros((len(valid_genos), self.n_states))
                    for i, (geno, marker) in enumerate(zip(valid_genos, valid_markers, strict=False)):
                        emissions[i] = self._compute_emission_probs(geno, marker)
                    all_data.append((emissions, positions, chrom))

        if not all_data:
            logger.warning("No valid data for Baum-Welch estimation")
            return {
                "recombination_rate": self.recombination_rate,
                "genotyping_error": self.genotyping_error,
                "log_likelihoods": [],
                "converged": False,
                "n_iterations": 0,
            }

        log_likelihoods = []
        prev_ll = -np.inf

        for iteration in range(max_iterations):
            total_log_likelihood = 0.0
            total_transitions = 0
            total_recombinations = 0.0

            for emissions, positions, chrom in all_data:
                T = len(positions)
                transitions = self._compute_transition_matrix(positions, chrom)
                initial = np.ones(self.n_states) / self.n_states

                # E-step: Forward-backward
                alpha, ll = self._forward_algorithm(emissions, transitions, initial)
                total_log_likelihood += ll

                scale = alpha.sum(axis=1)
                scale[scale == 0] = 1.0
                beta = self._backward_algorithm(emissions, transitions, scale)

                posteriors = alpha * beta
                row_sums = posteriors.sum(axis=1, keepdims=True)
                row_sums[row_sums == 0] = 1.0
                posteriors /= row_sums

                # Compute xi (transition posteriors)
                for t in range(T - 1):
                    xi = np.zeros((self.n_states, self.n_states))
                    for i in range(self.n_states):
                        for j in range(self.n_states):
                            xi[i, j] = (
                                alpha[t, i]
                                * transitions[t, i, j]
                                * emissions[t + 1, j]
                                * beta[t + 1, j]
                            )
                    xi_sum = xi.sum()
                    if xi_sum > 0:
                        xi /= xi_sum

                    # Count off-diagonal transitions (recombinations)
                    for i in range(self.n_states):
                        for j in range(self.n_states):
                            if i != j:
                                total_recombinations += xi[i, j]
                    total_transitions += 1

            log_likelihoods.append(total_log_likelihood)

            # Check convergence
            ll_change = total_log_likelihood - prev_ll
            logger.debug(
                f"Baum-Welch iteration {iteration + 1}: "
                f"log-likelihood = {total_log_likelihood:.4f}, "
                f"change = {ll_change:.6f}"
            )

            if abs(ll_change) < convergence_threshold:
                logger.info(f"Baum-Welch converged after {iteration + 1} iterations")
                return {
                    "recombination_rate": self.recombination_rate,
                    "genotyping_error": self.genotyping_error,
                    "log_likelihoods": log_likelihoods,
                    "converged": True,
                    "n_iterations": iteration + 1,
                }

            prev_ll = total_log_likelihood

            # M-step: Update recombination rate
            if total_transitions > 0:
                # Average recombination probability
                avg_recomb_prob = total_recombinations / (total_transitions * self.n_states)
                # Convert back to per-bp rate (approximate)
                avg_distance = np.mean([
                    np.mean(np.diff(pos)) for _, pos, _ in all_data if len(pos) > 1
                ])
                if avg_distance > 0 and avg_recomb_prob > 0 and avg_recomb_prob < 0.5:
                    # Inverse Haldane
                    new_rate = -np.log(1 - 2 * avg_recomb_prob) / (2 * avg_distance)
                    new_rate = max(1e-10, min(1e-6, new_rate))
                    self.recombination_rate = new_rate

        logger.info(f"Baum-Welch did not converge after {max_iterations} iterations")
        return {
            "recombination_rate": self.recombination_rate,
            "genotyping_error": self.genotyping_error,
            "log_likelihoods": log_likelihoods,
            "converged": False,
            "n_iterations": max_iterations,
        }


def run_hmm_inference(
    marker_genotypes: dict[str, SampleMarkerGenotypes],
    diagnostic_markers: DiagnosticMarkerSet,
    founders: list[str] | None = None,
    ploidy: int = 2,
    recombination_rate: float = 1e-8,
    genotyping_error: float = 0.01,
    genetic_map: GeneticMap | None = None,
) -> HMMResults:
    """Run HMM inference on marker genotypes.

    Convenience function wrapping HaplotypeHMM.

    Args:
        marker_genotypes: Dict mapping sample names to marker genotypes
        diagnostic_markers: Set of diagnostic markers
        founders: List of founder names (default: from markers)
        ploidy: Sample ploidy
        recombination_rate: Per-bp recombination rate
        genotyping_error: Genotyping error rate
        genetic_map: Optional genetic map

    Returns:
        HMMResults with inference results
    """
    if founders is None:
        founders = diagnostic_markers.founders

    hmm = HaplotypeHMM(
        founders=founders,
        ploidy=ploidy,
        recombination_rate=recombination_rate,
        genotyping_error=genotyping_error,
        genetic_map=genetic_map,
    )

    return hmm.fit_predict(marker_genotypes, diagnostic_markers)
