use pyo3::prelude::*;

#[pymodule]
mod ascutil {
    use pyo3::prelude::*;
    use std::path::PathBuf;
    use crate::circuit::Circuit;

    /// Mutates a circuit.asc in place.
    /// # Arguments
    /// * 'fpath' - path to circuit
    /// * 'rows' - List of 0 indexed rows to mutate on [0-15]
    /// * 'columns' - List of 0 indexed columns to mutate on [0-53]
    /// * 'mutation_chance' - chance to flip bit [0-1]
    #[pyfunction]
    fn mutate(fpath: PathBuf, rows: Vec<u8>, columns: Vec<u8>, mutation_chance: f32) -> Option<i32> {
        let mut c: Circuit = Circuit::new(fpath, mutation_chance, rows, columns);
        c.mutate();
        None
    }
}

pub mod circuit {
    use std::{fs::OpenOptions, path::PathBuf};
    const ROW_CHARS: u8 = 54 + 1;
    const NUM_ROWS: u8 = 16;

    use memmap2::MmapMut;
    use rand::{distr::{uniform::{UniformFloat, UniformSampler}}, rngs::ThreadRng};
    pub struct Circuit {
        mmap: MmapMut,
        index: usize,
        rows: Vec<u8>,
        columns: Vec<u8>,
        rng: ThreadRng,
        uf: UniformFloat<f64>,
        mutation_chance: f32
    }

    impl Circuit {
        pub fn new(fpath: PathBuf, mutation_chance: f32, rows: Vec<u8>, columns: Vec<u8>) -> Circuit {
            let file = OpenOptions::new().read(true).write(true).open(fpath).expect("Failed to open circuit");
            let mmap = unsafe {
                MmapMut::map_mut(&file).expect("Failed to mmap circuit")
            };

            Circuit { mmap: mmap, mutation_chance, index: 0, rows: rows, columns: columns, rng: rand::rng(), uf: UniformFloat::new(0.0, 1.0).unwrap()}
        }

        fn next_available(&self) -> bool {
            self.mmap.len() > self.index
        }

        fn characters_available(&self, amount: usize) -> bool {
            self.mmap.len() >= self.index + amount - 1

        }

        /// Moves cursor to first character after next newline
        fn next_line(&mut self) -> bool {
            if !self.next_available() {
                return false;
            }


            while self.mmap[self.index] != b'\n' {
                self.index += 1;

                if !self.next_available() {
                    return false;
                }
            }

            self.index += 1;
            true
        }

        /// Whether the cursor is at a logic tile
        fn check_logic_tile(&self) -> bool {
            if !self.characters_available(b".logic_tile".len()) {
                return false;
            }

            let mut i: usize = 0;
            for b in b".logic_tile".iter() {
                if self.mmap[self.index + i] != *b {
                   return false;
                }
                i += 1;
            }
            return true;
        }

        /// Moves cursor to first bit of next logic tile. Returns false if
        /// there are no more logic tiles.
        fn goto_logic_tile(&mut self) -> bool {
            while self.characters_available(b".logic_tile".len()) {
                if self.check_logic_tile() {
                    self.next_line();
                    return true;
                }

                if !self.next_line() {
                    return false;
                }
            }

            false
        }

        /// Mutates logic tile. Assumes cursor is at first bit of logic tile. Moves cursor to
        /// next line after logic tile afterwards.
        fn mutate_tile(&mut self) {
            for col in &self.columns {
                for row in &self.rows {
                    if self.uf.sample(&mut self.rng) > self.mutation_chance.into() {
                        continue;
                    }

                    let location = self.index + *col as usize + *row as usize * ROW_CHARS as usize;
                    if self.mmap[location] == b'0' {
                        self.mmap[location] = b'1';
                    } else {
                        self.mmap[location] = b'0';
                    }

                }
            }

            for _ in 0..NUM_ROWS {
                self.next_line();
            }
        }

        pub fn mutate(&mut self) {
            while self.goto_logic_tile() {
                self.mutate_tile();
            }

            let _ = self.mmap.flush();
        }
    }
}