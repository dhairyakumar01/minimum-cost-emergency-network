import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class DashboardScreen extends StatefulWidget {
  final Function(int) onNavigate;

  const DashboardScreen({super.key, required this.onNavigate});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  SystemHealth? _health;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchHealth();
  }

  Future<void> _fetchHealth() async {
    setState(() => _loading = true);
    final h = await ApiService.checkHealth();
    if (mounted) {
      setState(() {
        _health = h;
        _loading = false;
      });
    }
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Backend API Server URL'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Enter the Flask backend or deployed Vercel API endpoint URL:',
              style: TextStyle(fontSize: 13, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'http://127.0.0.1:5000',
                prefixIcon: Icon(Icons.cloud_queue),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              ApiService.setBaseUrl(controller.text.trim());
              Navigator.pop(ctx);
              _fetchHealth();
            },
            child: const Text('Save & Reconnect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text('🚨 ', style: TextStyle(fontSize: 18)),
            Expanded(
              child: Text(
                'Bengaluru MST Network',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Server Connection Settings',
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Status',
            onPressed: _fetchHealth,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Strip
            Card(
              color: (_health?.isHealthy ?? false) ? const Color(0xFFF0FDF4) : const Color(0xFFFEF2F2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(
                  color: (_health?.isHealthy ?? false) ? const Color(0xFFBBF7D0) : const Color(0xFFFECACA),
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Row(
                  children: [
                    Icon(
                      (_health?.isHealthy ?? false) ? Icons.check_circle : Icons.warning_amber_rounded,
                      color: (_health?.isHealthy ?? false) ? AppTheme.accentEmerald : AppTheme.accentRed,
                      size: 20,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _loading
                            ? 'Checking backend connection...'
                            : (_health?.statusText ?? 'Offline'),
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: (_health?.isHealthy ?? false) ? const Color(0xFF166534) : const Color(0xFF991B1B),
                        ),
                      ),
                    ),
                    Text(
                      'Endpoint: ${ApiService.baseUrl}',
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Platform Hero Description
            const Text(
              'Platform Overview',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textMain),
            ),
            const SizedBox(height: 4),
            const Text(
              'Mathematical Minimum Cost Emergency Communication Network for Bengaluru BBMP area with 100% Kruskal & Prim algorithmic parity.',
              style: TextStyle(fontSize: 13, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 16),

            // KPI Grid
            LayoutBuilder(
              builder: (ctx, constraints) {
                final isWide = constraints.maxWidth > 600;
                return GridView.count(
                  crossAxisCount: isWide ? 4 : 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: isWide ? 1.6 : 1.1,
                  children: [
                    _buildKpiCard(
                      'Total Facilities',
                      '1,255',
                      'Hospitals, Fire, Police',
                      Icons.local_hospital_outlined,
                      const Color(0xFF2563EB),
                    ),
                    _buildKpiCard(
                      'Spanning Links',
                      '1,254',
                      '|V| - 1 exact tree',
                      Icons.hub_outlined,
                      AppTheme.sidebarDark,
                    ),
                    _buildKpiCard(
                      'Total MST Length',
                      '480.178 km',
                      'Optimal Haversine metric',
                      Icons.timeline_outlined,
                      AppTheme.accentAmber,
                    ),
                    _buildKpiCard(
                      'Parity Verified',
                      '100.0%',
                      'Kruskal ≡ Prim convergence',
                      Icons.verified_outlined,
                      AppTheme.accentEmerald,
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),

            // Quick Access Modules
            const Text(
              'Interactive Modules',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textMain),
            ),
            const SizedBox(height: 12),
            _buildModuleTile(
              title: 'Construction Simulator',
              subtitle: 'Step-by-step Kruskal and Prim execution on 1,255 facilities and 5.0 km incident graphs.',
              icon: Icons.play_circle_outline,
              color: AppTheme.accentNavy,
              onTap: () => widget.onNavigate(2),
            ),
            const SizedBox(height: 10),
            _buildModuleTile(
              title: 'Emergency Simulation & Dispatch',
              subtitle: '6-Step multi-criteria emergency response routing with 3 optimization modes.',
              icon: Icons.emergency_outlined,
              color: AppTheme.accentRed,
              onTap: () => widget.onNavigate(3),
            ),
            const SizedBox(height: 10),
            _buildModuleTile(
              title: 'Facilities Directory',
              subtitle: 'Search and inspect all 1,255 verified emergency stations across Bengaluru.',
              icon: Icons.location_city_outlined,
              color: AppTheme.sidebarDark,
              onTap: () => widget.onNavigate(1),
            ),
            const SizedBox(height: 10),
            _buildModuleTile(
              title: 'Results & Statistics',
              subtitle: 'Empirical runtime analysis, theoretical complexity, and zero-violation invariants.',
              icon: Icons.bar_chart_outlined,
              color: AppTheme.accentEmerald,
              onTap: () => widget.onNavigate(4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKpiCard(
    String label,
    String value,
    String subtitle,
    IconData icon,
    Color accentColor,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Icon(icon, color: accentColor, size: 18),
              ],
            ),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(
                value,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: accentColor,
                ),
              ),
            ),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModuleTile({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withAlpha(30),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: color, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textMain),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppTheme.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}
