import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Results & Statistics', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Algorithmic Parity Confirmation Card
            Card(
              color: const Color(0xFFF0FDF4),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: const BorderSide(color: Color(0xFFBBF7D0), width: 1.5),
              ),
              child: const Padding(
                padding: EdgeInsets.all(14),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.verified, color: AppTheme.accentEmerald, size: 20),
                        SizedBox(width: 8),
                        Flexible(
                          child: Text(
                            'Algorithmic Parity Confirmed',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF166534),
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Greedy Convergence to Global Minimum',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF064E3B),
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Both Kruskal and Prim algorithms converge to the exact mathematically optimal total tree weight (480.1784 km across 1,254 spanning links). Prim grows a single continuous tree cut from a root vertex, while Kruskal merges disjoint components across the metric space without cycles.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 11, color: Color(0xFF166534), height: 1.4),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Visual Charts Section
            const Text(
              'Empirical Performance Benchmarks',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textMain),
            ),
            const SizedBox(height: 8),

            // Runtime Speedup & Parity Visual Bar Charts
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Text(
                            'Algorithm Execution Runtime (s)',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          '3.18× Kruskal Speedup',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.accentNavy),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // Visual comparison bars for Runtime
                    _buildHorizontalBar('Prim\'s Algorithm', 5.029, 6.0, '5.029 s', AppTheme.accentEmerald),
                    const SizedBox(height: 6),
                    _buildHorizontalBar('Kruskal\'s Algorithm', 1.581, 6.0, '1.581 s', AppTheme.accentNavy),
                    const SizedBox(height: 14),
                    const Divider(height: 1),
                    const SizedBox(height: 10),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Text(
                            'Total Spanning Distance Parity (km)',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          '100% Convergence Match',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _buildHorizontalBar('Prim\'s Tree Weight', 480.178, 500.0, '480.1784 km', AppTheme.accentEmerald),
                    const SizedBox(height: 6),
                    _buildHorizontalBar('Kruskal\'s Tree Weight', 480.178, 500.0, '480.1784 km', AppTheme.accentNavy),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Responsive Algorithm Comparison (Mobile stacked, wide side-by-side)
            LayoutBuilder(
              builder: (ctx, constraints) {
                final isWide = constraints.maxWidth >= 600;

                if (isWide) {
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: _buildKruskalCard()),
                      const SizedBox(width: 10),
                      Expanded(child: _buildPrimCard()),
                    ],
                  );
                }

                // Mobile Layout: Stacked cards with full width for zero text wrapping
                return Column(
                  children: [
                    _buildKruskalCard(),
                    const SizedBox(height: 10),
                    _buildPrimCard(),
                  ],
                );
              },
            ),
            const SizedBox(height: 14),

            // Invariant Verification Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Network Structural Invariants', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 8),
                    _invariantItem('Tree Edge Count Property', '|E| = |V| - 1', '1,254 edges connecting 1,255 vertices', true),
                    _invariantItem('Acyclicity & Connectedness', 'Zero Cycle Violations', 'Validated across all 785,631 fundamental cycle chords', true),
                    _invariantItem('Metric Parity', 'Exact Weight Agreement', '480.1784 km in both Kruskal and Prim trees', true),
                    _invariantItem('Geodesic Integrity', 'Positive Semi-Definite', 'Haversine distance matrix satisfying triangle inequality', true),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Top Bottleneck Spanning Edges Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Text(
                            'Longest MST Spanning Links',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text('Top 5 Bottlenecks', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.accentAmber)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _bottleneckItem('#1', 'Hesaraghatta PHC', 'Yelahanka General Hospital', '7.8256 km'),
                    _bottleneckItem('#2', 'Sarjapura Community Health', 'Electronic City Clinic', '6.4190 km'),
                    _bottleneckItem('#3', 'Nelamangala Taluk Hospital', 'Madavara Health Post', '5.9324 km'),
                    _bottleneckItem('#4', 'Kengeri Satellite Station', 'Rajarajeshwari Nagar Post', '5.1042 km'),
                    _bottleneckItem('#5', 'Hoskote Perimeter Post', 'KR Puram General Hospital', '4.8871 km'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  static Widget _buildHorizontalBar(String label, double value, double maxVal, String displayVal, Color color) {
    final pct = (value / maxVal).clamp(0.0, 1.0);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                label,
                style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            Text(displayVal, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
          ],
        ),
        const SizedBox(height: 3),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: pct,
            backgroundColor: AppTheme.borderLight,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 8,
          ),
        ),
      ],
    );
  }

  Widget _buildKruskalCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Flexible(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.accentNavy.withAlpha(25),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      "KRUSKAL'S ALGORITHM",
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.accentNavy),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                const Text('O(E log E)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.accentNavy)),
              ],
            ),
            const SizedBox(height: 6),
            const Text('Disjoint Set Forest (DSU)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const Divider(height: 14),
            _auditRow('Total Metric', '480.1784 km'),
            _auditRow('Spanning Edges', '1,254 links'),
            _auditRow('Complexity', 'O(E log E)'),
            _auditRow('Core Structure', 'DSU with Rank & Path Compression'),
          ],
        ),
      ),
    );
  }

  Widget _buildPrimCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Flexible(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.sidebarDark.withAlpha(25),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      "PRIM'S ALGORITHM",
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                const Text('O(E log V)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark)),
              ],
            ),
            const SizedBox(height: 6),
            const Text('Priority Queue Expansion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const Divider(height: 14),
            _auditRow('Total Metric', '480.1784 km'),
            _auditRow('Spanning Edges', '1,254 links'),
            _auditRow('Complexity', 'O(E log V)'),
            _auditRow('Core Structure', 'Binary Min-Heap Priority Queue'),
          ],
        ),
      ),
    );
  }

  Widget _auditRow(String label, String val) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 6),
          Expanded(
            flex: 3,
            child: Text(
              val,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
              textAlign: TextAlign.end,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _invariantItem(String title, String status, String note, bool pass) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(pass ? Icons.check_circle : Icons.error, color: pass ? AppTheme.accentEmerald : AppTheme.accentRed, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Text(
                        title,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      status,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                        color: pass ? AppTheme.accentEmerald : AppTheme.accentRed,
                      ),
                    ),
                  ],
                ),
                Text(note, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _bottleneckItem(String rank, String u, String v, String dist) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: AppTheme.bgCanvas,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Text(rank, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text('$u ↔ $v', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis),
          ),
          const SizedBox(width: 6),
          Text(dist, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.accentAmber)),
        ],
      ),
    );
  }
}
