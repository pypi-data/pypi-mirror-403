---
inclusion: always
---

# Rust Best Practices & Modern Standards

## Rust Version & Edition
- Target Rust 1.93.0 or later (released January 2026)
- Always use Rust Edition 2024 (latest stable edition)
- Set `edition = "2024"` in Cargo.toml
- Use `rust-version = "1.93"` in Cargo.toml to specify MSRV

## Code Style & Idioms
- Use `clippy` recommendations and fix all warnings
- Follow Rust naming conventions:
  - `snake_case` for functions, variables, modules
  - `PascalCase` for types, traits, enums
  - `SCREAMING_SNAKE_CASE` for constants
- Prefer `?` operator over explicit error handling
- Use `impl Trait` for return types when appropriate
- Leverage pattern matching instead of if-let chains
- Use `derive` macros for common traits (Debug, Clone, etc.)

## Error Handling
- Use `Result<T, E>` for recoverable errors
- Use `anyhow` or `thiserror` for error handling in applications
- Never use `unwrap()` or `expect()` in production code paths
- Propagate errors with `?` operator

## Performance
- Use `rayon` for parallel iteration when processing collections
- Prefer iterators over loops for better optimization
- Use `&str` over `String` when possible
- Avoid unnecessary cloning - use references
- Use `Vec::with_capacity()` when size is known

## Dependencies
- Keep dependencies minimal and well-maintained
- Pin versions in Cargo.toml for reproducibility
- Use workspace dependencies for multi-crate projects
- Prefer crates from trusted sources

## Project Structure
- Keep `main.rs` minimal - delegate to library code
- Separate concerns into modules
- Use `mod.rs` or module files appropriately
- Write unit tests in the same file with `#[cfg(test)]`

## CLI Best Practices
- Use `clap` v4+ with derive macros for argument parsing
- Provide helpful error messages
- Support `--help` and `--version` flags
- Use progress bars for long operations (indicatif crate)
- Handle Ctrl+C gracefully

## Documentation & Research
- ALWAYS check official documentation from docs.rs or crates.io before implementing
- Use web search to find latest crate documentation and best practices
- Read the official Rust documentation for language features
- Check crate README and examples before using new dependencies
- Verify API usage patterns from official sources, not assumptions
- For image processing: consult `image` crate docs at https://docs.rs/image/
- For CLI parsing: consult `clap` crate docs at https://docs.rs/clap/
- For parallelization: consult `rayon` crate docs at https://docs.rs/rayon/

## Image Processing Specifics
- Use `image` crate for format support
- Use `rayon` for parallel batch processing
- Handle common formats: PNG, JPG, WebP
- Validate input before processing
- Provide compression quality options
