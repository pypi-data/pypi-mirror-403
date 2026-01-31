#[cfg(test)]
mod tests {
    use crate::block::block::Block;
    use crate::pow::difficulty::Difficulty;
    use std::time::Instant;

    fn measure(diff: Difficulty) -> f64 {
        let runs = 10;
        let mut timings = Vec::with_capacity(runs);
        for _ in 0..runs {
            let mut block = Block::new(1, vec![0u8; 32], diff.clone(), vec![], vec![], String::new());
            let start = Instant::now();
            block.mine();
            timings.push(start.elapsed().as_secs_f64() * 1000.0);
        }
        timings.sort_by(|a, b| a.partial_cmp(b).unwrap());
        timings[runs / 2] // Median
    }

    fn new_diff(t: u32, m: u32, p: u8, bits: u8) -> Difficulty {
        Difficulty {
            t_cost: t,
            m_cost: m,
            p_cost: p,
            n_bits: bits,
            hash_len_chars: 32,
            compression_level: 9,
            compression_type: 0,
            express: 0,
        }
    }

    #[test]
    fn analyze_pow_parameters() {
        println!("\n--- PoW Parameter Analysis high-res ---");

        // 1. T-Cost Analysis (Linearity)
        println!("\nT-Cost Granularity (m=8, p=1, bits=1):");
        for t in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 30] {
            let time = measure(new_diff(t, 8, 1, 1));
            println!("T={:<2} | Time: {:.4} ms", t, time);
        }

        // 2. M-Cost Analysis (Granularity)
        println!("\nM-Cost Granularity (t=1, p=1, bits=1):");
        for m in [8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64] {
            let time = measure(new_diff(1, m, 1, 1));
            println!("M={:<2} | Time: {:.4} ms", m, time);
        }

        // 3. Bits Analysis (Granularity)
        println!("\nBits Granularity (t=1, m=8, p=1):");
        for b in [1, 2, 4, 6, 8, 10, 12, 14, 16] {
            let time = measure(new_diff(1, 8, 1, b));
            println!("Bits={:<2} | Time: {:.4} ms", b, time);
        }
    }
}
