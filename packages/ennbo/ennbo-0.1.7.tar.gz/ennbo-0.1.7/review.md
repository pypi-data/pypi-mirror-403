# Review: HNSW Implementation vs Proposal

This review compares the current implementation of `ENNIndex` and `EpistemicNearestNeighbors` against the proposal in `hnsw.md`.

## Summary
The implementation successfully matches the core architectural goals of the proposal. It introduces `ENNIndexDriver`, supports `IndexHNSWFlat`, and maintains `IndexFlatL2` as the default.

## Detailed Comparison

### 1. Enum Driver Selection
- **Proposal**: Introduce `ENNIndexDriver` Enum with `FLAT` and `HNSW`.
- **Implementation**: `src/enn/turbo/config/enn_index_driver.py` defines `ENNIndexDriver` with `FLAT` and `HNSW`.
- **Status**: **Matched.**

### 2. ENNIndex Persistence and Incremental Support
- **Proposal**: Update `ENNIndex` to handle both modes and support an `add()` method.
- **Implementation**: 
    - `ENNIndex.__init__` now accepts a `driver`.
    - `ENNIndex.add()` is implemented and correctly handles both `FLAT` and `HNSW` by adding to the underlying FAISS index.
    - `ENNIndex._build_index()` correctly switches between `IndexFlatL2` and `IndexHNSWFlat`.
- **Status**: **Matched.**

### 3. Maintaining Default Behavior
- **Proposal**: `IndexFlatL2` should remain the default and be rebuilt every time in the standard flow.
- **Implementation**:
    - `EpistemicNearestNeighbors.__init__` defaults `index_driver` to `ENNIndexDriver.FLAT`.
    - `ENNIndex.__init__` defaults `driver` to `ENNIndexDriver.FLAT`.
    - The standard `mk_enn` flow (used in `turbo`) still creates a new `EpistemicNearestNeighbors` on every `fit()`, which in turn creates a new `ENNIndex`. This preserves the "rebuild every time" behavior for the default driver.
- **Status**: **Matched.**

### 4. Incremental API in ENN
- **Implementation Note**: `EpistemicNearestNeighbors` now has an `add()` method that updates both the training data and the internal `ENNIndex`. This enables true incremental growth if the `EpistemicNearestNeighbors` object is persisted, which was a key motivation for the HNSW support.
- **Status**: **Exceeded.** (The proposal focused on the index level; the implementation correctly exposed it at the model level).

## Observations & Recommendations
1. **Configurability**: As noted in the code comments (`TODO: Make M configurable`), the HNSW parameters (like `M` and `efConstruction`) are currently hardcoded to 32. These should eventually be moved to a configuration object.
2. **Consistency**: The `add()` method in `EpistemicNearestNeighbors` handles `yvar` consistency with a `ValueError`, which is appropriate for maintaining algorithmic integrity.
3. **Efficiency**: The implementation uses `astype(np.float32, copy=False)` which aligns with the "Efficiency & Scaling" principles in `style.md`.

## Conclusion
The implementation is highly compliant with the `hnsw.md` proposal.
