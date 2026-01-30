//! Benchmarks for qodacode_core algorithms
//!
//! Run with: cargo bench

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use qodacode_core::{
    fingerprint::compute_fingerprint,
    similarity::{levenshtein_distance, compute_similarity_score, is_homoglyph_attack},
    patterns::is_safe_pattern,
};

fn benchmark_fingerprint(c: &mut Criterion) {
    let filepath = "src/config/settings.py";
    let rule_id = "SEC-001";
    let snippet = "api_key = 'sk-ant-api03-AbCdEf123456789-very-long-secret-key-here'";

    c.bench_function("compute_fingerprint", |b| {
        b.iter(|| {
            compute_fingerprint(
                black_box(filepath),
                black_box(rule_id),
                black_box(snippet),
            )
        })
    });
}

fn benchmark_levenshtein(c: &mut Criterion) {
    let s1 = "requests";
    let s2 = "reqeusts";

    c.bench_function("levenshtein_distance_short", |b| {
        b.iter(|| levenshtein_distance(black_box(s1), black_box(s2)))
    });

    let long1 = "this_is_a_very_long_package_name_for_testing";
    let long2 = "this_is_a_very_lomg_package_name_for_testing";

    c.bench_function("levenshtein_distance_long", |b| {
        b.iter(|| levenshtein_distance(black_box(long1), black_box(long2)))
    });
}

fn benchmark_similarity(c: &mut Criterion) {
    let suspicious = "reqeusts";
    let legitimate = "requests";

    c.bench_function("compute_similarity_score", |b| {
        b.iter(|| {
            compute_similarity_score(black_box(suspicious), black_box(legitimate))
        })
    });
}

fn benchmark_homoglyph(c: &mut Criterion) {
    // Cyrillic 'е' in "rеquests"
    let suspicious = "rеquests";
    let legitimate = "requests";

    c.bench_function("is_homoglyph_attack", |b| {
        b.iter(|| {
            is_homoglyph_attack(black_box(suspicious), black_box(legitimate))
        })
    });
}

fn benchmark_pattern_matching(c: &mut Criterion) {
    let snippet = "api_key = os.environ.get('API_KEY') or decrypt(encrypted_key)";
    let filepath = "src/config.py";

    c.bench_function("is_safe_pattern", |b| {
        b.iter(|| {
            is_safe_pattern(black_box(snippet), black_box(filepath))
        })
    });

    let long_snippet = r#"
        def configure():
            api_key = os.environ.get('API_KEY')
            secret = decrypt(load_encrypted())
            db_url = settings.DATABASE_URL
            return Config(api_key, secret, db_url)
    "#;

    c.bench_function("is_safe_pattern_long", |b| {
        b.iter(|| {
            is_safe_pattern(black_box(long_snippet), black_box(filepath))
        })
    });
}

criterion_group!(
    benches,
    benchmark_fingerprint,
    benchmark_levenshtein,
    benchmark_similarity,
    benchmark_homoglyph,
    benchmark_pattern_matching,
);

criterion_main!(benches);
