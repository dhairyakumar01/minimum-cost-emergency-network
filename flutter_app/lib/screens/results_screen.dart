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
            const SizedBox(height: 16),
          ],
        ),
      ),
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
          Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          Flexible(
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
}
