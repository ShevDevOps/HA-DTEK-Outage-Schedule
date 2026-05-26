import typescript from '@rollup/plugin-typescript';
import nodeResolve from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';

export default {
  input: ['src/main.ts'],
  output: {
    file: 'dist/dtek-outage-card.js', // Це той самий файл, який піде в HA
    format: 'es',
  },
  plugins: [nodeResolve(), typescript(), terser()],
};