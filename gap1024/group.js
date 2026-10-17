/* group.js: invariants and presentations of a p-class-2 2-group, computed from its census record "K E f_1 ... f_E".
 *
 * Each f_l encodes a quadratic form on V = F_2^K. Bit i (i < K) is the coefficient of z_l in g_i^2; bit K + p(i,j) is
 * the coefficient of z_l in [g_i, g_j], with the pairs i < j numbered lexicographically from 0. The group is
 *   G = < g_1..g_K, z_1..z_E | z_l central of order 2, g_i^2 = prod z_l^(bit i), [g_i,g_j] = prod z_l^(bit K+p(i,j)) >,
 * of order 2^(K+E), with Frattini subgroup W = <z_1..z_E> central and G/W = V. Everything below is linear algebra over F_2
 * on these bits; the only enumerations are over V (2^K vectors) and over the dual of W (2^E vectors).
 * Works in the browser (window.GAP1024) and in Node (module.exports).
 */
(function (root) {
  'use strict';

  const popcount = (x) => { let c = 0; while (x) { x &= x - 1; c++; } return c; };
  const parity = (x) => popcount(x) & 1;
  const log2 = (n) => Math.round(Math.log2(n));

  // rank over F_2 of a list of bit-vectors (BigInt or Number); basis kept with distinct leading bits
  function rank(vs) {
    const basis = [];
    for (let v of vs) {
      for (const b of basis) if ((v ^ b) < v) v ^= b;
      if (v) { basis.push(v); basis.sort((a, b) => (a > b ? -1 : a < b ? 1 : 0)); }
    }
    return basis.length;
  }

  // 0 <= i < j < K
  function pairIndex(K, i, j) { return i * K - (i * (i + 1)) / 2 + (j - i - 1); }

  function parseRecord(text) {
    const parts = String(text).trim().split(/[\s,.]+/).filter(Boolean);
    if (parts.length < 3) throw new Error('A record looks like "K E f_1 ... f_E", for example "6 4 32 16 8 7".');
    if (!parts.every((p) => /^[0-9]+$/.test(p))) throw new Error('A record contains non-negative integers only.');
    const K = Number(parts[0]), E = Number(parts[1]);
    if (!(K >= 1 && K <= 10)) throw new Error('K (the number of generators) must be between 1 and 10.');
    const N = (K * (K + 1)) / 2;
    if (!(E >= 1 && E <= Math.min(N, 12))) throw new Error(`E must be between 1 and ${Math.min(N, 12)} when K = ${K}.`);
    if (parts.length !== 2 + E) throw new Error(`Expected ${E} forms after "${K} ${E}", found ${parts.length - 2}.`);
    const forms = parts.slice(2).map((s) => BigInt(s));
    const lim = 1n << BigInt(N);
    for (const f of forms) if (f <= 0n || f >= lim) throw new Error(`Each form must be an integer from 1 to 2^${N} - 1.`);
    if (rank(forms) !== E) throw new Error('The forms are linearly dependent, so this is not a valid record.');
    return { K, E, N, forms };
  }

  // all elements of the span of a list of W-vectors
  function spanOf(gens) {
    const basis = [];
    for (let g of gens) { for (const b of basis) if ((g ^ b) < g) g ^= b; if (g) { basis.push(g); basis.sort((a, b) => b - a); } }
    const out = [0];
    for (const b of basis) { const n = out.length; for (let t = 0; t < n; t++) out.push(out[t] ^ b); }
    return out;
  }

  function analyse(text) {
    const { K, E, N, forms } = parseRecord(text);
    const VN = 1 << K, WN = 1 << E, order = 2 ** (K + E);

    // squares and commutators as vectors in W (E-bit masks): sqW[i] = g_i^2, comW[i][j] = [g_i, g_j]
    const bit = (l, b) => Number((forms[l] >> BigInt(b)) & 1n);
    const sqW = Array.from({ length: K }, (_, i) => { let m = 0; for (let l = 0; l < E; l++) m |= bit(l, i) << l; return m; });
    const comW = Array.from({ length: K }, () => new Array(K).fill(0));
    for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) {
      let m = 0; for (let l = 0; l < E; l++) m |= bit(l, K + pairIndex(K, i, j)) << l;
      comW[i][j] = comW[j][i] = m;
    }
    // q[v] = the square of every element over v; bcol[v][t] = beta(v, e_t), the commutator of v with g_t
    const q = new Array(VN).fill(0), bcol = Array.from({ length: VN }, () => new Array(K).fill(0));
    for (let v = 1; v < VN; v++) {
      const i = 31 - Math.clz32(v), u = v ^ (1 << i);          // v = u + e_i, i the top bit of v
      let cross = 0; for (let t = 0; t < i; t++) if ((u >> t) & 1) cross ^= comW[t][i];
      q[v] = q[u] ^ sqW[i] ^ cross;                              // q(u + e_i) = q(u) + q(e_i) + beta(u, e_i)
      for (let t = 0; t < K; t++) bcol[v][t] = bcol[u][t] ^ comW[i][t];
    }
    const derivedGens = []; for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) if (comW[i][j]) derivedGens.push(comW[i][j]);
    const j = rank(derivedGens), k = E - j;

    // c(v) = rank of u -> beta(v, u): the elements over v form 2^(E - c(v)) classes of size 2^c(v)
    const c = bcol.map((cols) => rank(cols));
    const R = [], zeroQ = [], classSizes = new Map(); let nClasses = 0;
    for (let v = 0; v < VN; v++) {
      if (c[v] === 0) R.push(v);
      if (q[v] === 0) zeroQ.push(v);
      const n = 2 ** (E - c[v]); nClasses += n; classSizes.set(2 ** c[v], (classSizes.get(2 ** c[v]) || 0) + n);
    }
    const r = log2(R.length);                                     // Z(G) = preimage of the radical R
    const s = rank(R.map((v) => q[v]));                           // q is additive on R; s = rank of squaring on Z(G)
    const d = rank([...derivedGens, ...R.map((v) => q[v])]) - j;  // d = log2 |Z(G)^2 G' : G'|
    const omega1 = rank(zeroQ);                                   // Omega_1(G) = preimage of span{v : q(v) = 0}

    // the set of commutators [x, y] is the union over v of the images of beta(v, .)
    const isComm = new Uint8Array(WN);
    for (let v = 0; v < VN; v++) for (const x of spanOf(bcol[v])) isComm[x] = 1;
    const commSet = []; for (let x = 0; x < WN; x++) if (isComm[x]) commSet.push(x);
    let width = 0;                                                // least n: every element of G' is a product of n commutators
    for (let reach = new Set([0]); reach.size < 2 ** j || width === 0; width++) {   // at least 1, as GAP's CommutatorLength
      const next = new Set(); for (const a of reach) for (const x of commSet) next.add(a ^ x); reach = next;
    }

    // irreducible characters: over lambda in W*, rank 2t of lambda.beta gives 2^(K-2t) characters of degree 2^t
    const charDegrees = new Map();
    for (let lam = 0; lam < WN; lam++) {
      const B = new Array(K).fill(0);
      for (let i = 0; i < K; i++) for (let t = 0; t < K; t++) if (parity(comW[i][t] & lam)) B[i] |= 1 << t;
      const t = rank(B) / 2;
      charDegrees.set(2 ** t, (charDegrees.get(2 ** t) || 0) + 2 ** (K - 2 * t));
    }

    // maximal subgroups = preimages of the hyperplanes ker(a); abelian iff beta vanishes on a basis of ker(a)
    let abelianMaximal = 0;
    for (let a = 1; a < VN; a++) {
      const p = 31 - Math.clz32(a & -a), H = [];
      for (let t = 0; t < K; t++) if (t !== p) H.push((a >> t) & 1 ? (1 << t) | (1 << p) : 1 << t);
      let ab = true;
      for (let x = 0; x < H.length && ab; x++) for (let y = x + 1; y < H.length && ab; y++) {
        let w = 0; for (let t = 0; t < K; t++) if ((H[y] >> t) & 1) w ^= bcol[H[x]][t];
        if (w) ab = false;
      }
      if (ab) abelianMaximal++;
    }

    const involutions = zeroQ.length * WN - 1, abelian = j === 0, special = r === 0 && j === E;
    return {
      K, E, N, order, record: `${K} ${E} ${forms.join(' ')}`,
      j, k, r, s, d, rank: K, frattini: fmtAbelian(0, E),
      derivedOrder: 2 ** j, derived: fmtAbelian(0, j), abelianization: fmtAbelian(k, K - k),
      centreOrder: 2 ** (E + r), centre: fmtAbelian(s, E + r - 2 * s), inner: fmtAbelian(0, K - r),
      omega1Order: 2 ** (E + omega1), nilpotencyClass: abelian ? 1 : 2, derivedLength: abelian ? 1 : 2, exponent: 4,
      abelian, special, extraspecial: special && E === 1,
      extraspecialSign: special && E === 1 ? (zeroQ.length > VN / 2 ? '+' : '−') : null,
      camina: special && j > 0 && c.every((cv, v) => v === 0 || cv === j),
      directC2: r - s, nClasses, breadth: Math.max(...c),
      classSizes: [...classSizes.entries()].sort((a, b) => a[0] - b[0]),
      charDegrees: [...charDegrees.entries()].sort((a, b) => a[0] - b[0]), linearCharacters: 2 ** (K + k),
      involutions, order4: order - 1 - involutions, centralInvolutions: 2 ** (E + r - s) - 1,
      commutators: commSet.length, commutatorWidth: width,
      maximalSubgroups: VN - 1, abelianMaximal, commutingProbability: nClasses / order,
      pc: pcPresentation(K, E, sqW, comW), small: smallPresentation(K, E, forms),
    };
  }

  function fmtAbelian(a4, a2) {
    const parts = [];
    if (a4) parts.push(a4 === 1 ? 'C4' : `C4^${a4}`);
    if (a2) parts.push(a2 === 1 ? 'C2' : `C2^${a2}`);
    return parts.length ? parts.join(' × ') : '1';
  }

  // power-commutator presentation on g_1..g_K, z_1..z_E
  function pcPresentation(K, E, sqW, comW) {
    const z = (m) => { const t = []; for (let l = 0; l < E; l++) if ((m >> l) & 1) t.push(`z${l + 1}`); return t.length ? t.join('·') : '1'; };
    const rels = [];
    for (let i = 0; i < K; i++) rels.push([`g${i + 1}^2`, z(sqW[i])]);
    for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) if (comW[i][j]) rels.push([`[g${i + 1}, g${j + 1}]`, z(comW[i][j])]);
    return { generators: K + E, relations: rels };
  }

  // presentation on g_1..g_K alone: reduce the forms to echelon form with pivots at the highest bits; the square or
  // commutator at each pivot bit is a central involution named z_l, and every other square or commutator is a product of those
  function smallPresentation(K, E, forms) {
    const N = (K * (K + 1)) / 2, rows = forms.slice(), piv = [];
    for (let c = N - 1, ri = 0; c >= 0 && ri < E; c--) {
      const b = 1n << BigInt(c);
      let p = -1; for (let t = ri; t < E; t++) if (rows[t] & b) { p = t; break; }
      if (p < 0) continue;
      [rows[ri], rows[p]] = [rows[p], rows[ri]];
      for (let t = 0; t < E; t++) if (t !== ri && (rows[t] & b)) rows[t] ^= rows[ri];
      piv.push(c); ri++;
    }
    const pairs = []; for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) pairs.push([i, j]);
    const term = (b) => (b < K ? { txt: `g${b + 1}^2`, gap: `g${b + 1}^2` }
      : { txt: `[g${pairs[b - K][0] + 1}, g${pairs[b - K][1] + 1}]`, gap: `Comm(g${pairs[b - K][0] + 1}, g${pairs[b - K][1] + 1})` });
    const Z = piv.map(term), rels = [], gapRels = [];
    for (let b = 0; b < N; b++) {
      if (piv.includes(b)) continue;
      const t = []; for (let l = 0; l < E; l++) if ((rows[l] >> BigInt(b)) & 1n) t.push(l);
      if (b >= K && !t.length) { gapRels.push(term(b).gap); continue; }   // trivial commutator: implicit in the text, a relator in GAP
      rels.push([term(b).txt, t.length ? t.map((l) => Z[l].txt).join('·') : '1']);
      gapRels.push(t.length ? `${term(b).gap} / (${t.map((l) => Z[l].gap).join('*')})` : term(b).gap);
    }
    for (const zz of Z) { gapRels.push(`(${zz.gap})^2`); for (let i = 1; i <= K; i++) gapRels.push(`Comm(${zz.gap}, g${i})`); }
    const names = Array.from({ length: K }, (_, i) => `"g${i + 1}"`).join(', ');
    const gap = `F := FreeGroup(${names});; AssignGeneratorVariables(F);;\n` +
      `G := F / [ ${gapRels.join(',\n            ')} ];;\n` +
      `P := Image(EpimorphismPGroup(G, 2, 2));;   # the same group as a pc group; Size(P) = ${2 ** (K + E)}`;
    return { generators: K, central: Z.map((x) => x.txt), relations: rels, gapRelators: gapRels, gap };
  }

  const api = { parseRecord, analyse, pairIndex, rank };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.GAP1024 = api;
})(typeof window !== 'undefined' ? window : this);
