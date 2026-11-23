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
  List<Facility> _sampleFacilities = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchDashboardData();
  }

  Future<void> _fetchDashboardData() async {
    setState(() => _loading = true);
    final healthFuture = ApiService.checkHealth();
    final facilitiesFuture = ApiService.getFacilities();

    final results = await Future.wait([healthFuture, facilitiesFuture]);

    if (mounted) {
      setState(() {
        _health = results[0] as SystemHealth;
        _sampleFacilities = results[1] as List<Facility>;
        _loading = false;
      });
    }
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Backend API Server URL', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Enter the Flask backend or deployed Vercel API endpoint URL:',
              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'https://minimum-cost-emergency-network.vercel.app',
                prefixIcon: Icon(Icons.cloud_queue, size: 20),
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
              _fetchDashboardData();
            },
            child: const Text('Save & Reconnect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isOnline = _health?.isHealthy ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text('🚨 ', style: TextStyle(fontSize: 18)),
            Expanded(
              child: Text(
                'Bengaluru MST Network',
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, size: 20),
            tooltip: 'Server Connection',
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            tooltip: 'Refresh Status',
            onPressed: _fetchDashboardData,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Strip Card
            Card(
              color: isOnline ? const Color(0xFFF0FDF4) : const Color(0xFFFEF2F2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(
                  color: isOnline ? const Color(0xFFBBF7D0) : const Color(0xFFFECACA),
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: isOnline ? AppTheme.accentEmerald : AppTheme.accentRed,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _loading
                                ? 'Connecting to backend...'
                                : (isOnline ? 'System Operational • 1,255 Nodes' : 'Backend Disconnected'),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                              color: isOnline ? const Color(0xFF166534) : const Color(0xFF991B1B),
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: isOnline ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            isOnline ? 'ONLINE' : 'OFFLINE',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: isOnline ? const Color(0xFF166534) : const Color(0xFF991B1B),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Icon(Icons.cloud_done_outlined, size: 14, color: AppTheme.textMuted),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            ApiService.baseUrl,
                            style: const TextStyle(fontSize: 11, color: AppTheme.textMuted, fontFamily: 'monospace'),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Platform Hero Description
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: AppTheme.sidebarDark.withAlpha(25),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.account_tree_outlined, color: AppTheme.sidebarDark, size: 18),
                      ),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          'Platform Overview',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textMain),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Mathematical Minimum Cost Emergency Communication Network for Bengaluru BBMP area with 100% Kruskal & Prim algorithmic parity.',
                    style: TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Emergency Facility Composition Breakdown
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
                            'Facility Composition (1,255 Total)',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMain),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          'BBMP Area',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Proportional distribution bar
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 1097,
                            child: Container(height: 8, color: AppTheme.hospitalColor),
                          ),
                          Expanded(
                            flex: 138,
                            child: Container(height: 8, color: AppTheme.policeColor),
                          ),
                          Expanded(
                            flex: 20,
                            child: Container(height: 8, color: AppTheme.fireColor),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      alignment: WrapAlignment.spaceBetween,
                      children: [
                        _agencyBadge('1,097 Hospitals', '87.4%', AppTheme.hospitalColor),
                        _agencyBadge('138 Police', '11.0%', AppTheme.policeColor),
                        _agencyBadge('20 Fire', '1.6%', AppTheme.fireColor),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Responsive KPI Grid (safe aspect ratio, no vertical text overflow)
            LayoutBuilder(
              builder: (ctx, constraints) {
                final isWide = constraints.maxWidth > 600;
                return GridView.count(
                  crossAxisCount: isWide ? 4 : 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: isWide ? 1.6 : 1.35,
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
            const SizedBox(height: 14),

            // Spatial Network Distribution Mini-Map
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
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.map_outlined, size: 18, color: AppTheme.sidebarDark),
                              SizedBox(width: 6),
                              Flexible(
                                child: Text(
                                  'Spatial Network Overview',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMain),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        InkWell(
                          onTap: () => widget.onNavigate(1),
                          child: const Text(
                            'Open Full Map →',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      height: 140,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppTheme.borderLight),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: CustomPaint(
                          painter: MiniNetworkPainter(
                            facilities: _sampleFacilities,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(
                          child: Text(
                            '🔴 Hospital  •  🔵 Police  •  🟠 Fire Station',
                            style: TextStyle(fontSize: 10, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Quick Access Modules
            const Text(
              'Interactive Modules',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppTheme.textMain),
            ),
            const SizedBox(height: 10),
            _buildModuleTile(
              title: 'Construction Simulator',
              subtitle: 'Step-by-step Kruskal and Prim execution on 1,255 facilities and 5.0 km incident graphs.',
              icon: Icons.play_circle_outline,
              color: AppTheme.accentNavy,
              onTap: () => widget.onNavigate(2),
            ),
            const SizedBox(height: 8),
            _buildModuleTile(
              title: 'Emergency Simulation & Dispatch',
              subtitle: '6-Step multi-criteria emergency response routing with 3 optimization modes.',
              icon: Icons.emergency_outlined,
              color: AppTheme.accentRed,
              onTap: () => widget.onNavigate(3),
            ),
            const SizedBox(height: 8),
            _buildModuleTile(
              title: 'Facilities Directory',
              subtitle: 'Search and inspect all 1,255 verified emergency stations across Bengaluru.',
              icon: Icons.location_city_outlined,
              color: AppTheme.sidebarDark,
              onTap: () => widget.onNavigate(1),
            ),
            const SizedBox(height: 8),
            _buildModuleTile(
              title: 'Results & Statistics',
              subtitle: 'Empirical runtime analysis, theoretical complexity, and zero-violation invariants.',
              icon: Icons.bar_chart_outlined,
              color: AppTheme.accentEmerald,
              onTap: () => widget.onNavigate(4),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _agencyBadge(String label, String pct, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(shape: BoxShape.circle, color: color),
        ),
        const SizedBox(width: 4),
        Text(
          '$label ($pct)',
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
        ),
      ],
    );
  }

  Widget _buildKpiCard(String label, String value, String sub, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(5),
                  decoration: BoxDecoration(
                    color: color.withAlpha(25),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Icon(icon, size: 16, color: color),
                ),
              ],
            ),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(
                value,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppTheme.textMain),
              ),
            ),
            Text(
              sub,
              style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
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
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: color.withAlpha(25),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textMain),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted, height: 1.3),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}

class MiniNetworkPainter extends CustomPainter {
  final List<Facility> facilities;

  MiniNetworkPainter({required this.facilities});

  @override
  void paint(Canvas canvas, Size size) {
    // Grid lines for dark map aesthetic
    final gridPaint = Paint()
      ..color = Colors.white.withAlpha(12)
      ..strokeWidth = 0.5;

    for (int i = 1; i < 4; i++) {
      canvas.drawLine(Offset(0, size.height * (i / 4)), Offset(size.width, size.height * (i / 4)), gridPaint);
      canvas.drawLine(Offset(size.width * (i / 4), 0), Offset(size.width * (i / 4), size.height), gridPaint);
    }

    if (facilities.isEmpty) {
      // Draw subtle placeholder dots if loading
      final placeholderPaint = Paint()..color = const Color(0xFF38BDF8).withAlpha(100);
      canvas.drawCircle(Offset(size.width * 0.5, size.height * 0.5), 3, placeholderPaint);
      canvas.drawCircle(Offset(size.width * 0.4, size.height * 0.4), 2.5, placeholderPaint);
      canvas.drawCircle(Offset(size.width * 0.6, size.height * 0.6), 2.5, placeholderPaint);
      return;
    }

    const minLat = 12.80;
    const maxLat = 13.15;
    const minLon = 77.40;
    const maxLon = 77.80;

    double projectX(double lon) => ((lon - minLon) / (maxLon - minLon)) * size.width;
    double projectY(double lat) => size.height - (((lat - minLat) / (maxLat - minLat)) * size.height);

    final hospPaint = Paint()..color = AppTheme.hospitalColor.withAlpha(200);
    final polPaint = Paint()..color = AppTheme.policeColor.withAlpha(220);
    final firePaint = Paint()..color = AppTheme.fireColor;

    for (final f in facilities) {
      final x = projectX(f.longitude);
      final y = projectY(f.latitude);
      if (x >= 0 && x <= size.width && y >= 0 && y <= size.height) {
        Paint p = hospPaint;
        double radius = 1.6;
        if (f.agency == 'police' || f.agency == 'police_station') {
          p = polPaint;
          radius = 2.0;
        } else if (f.agency == 'fire' || f.agency == 'fire_station') {
          p = firePaint;
          radius = 2.4;
        }
        canvas.drawCircle(Offset(x, y), radius, p);
      }
    }
  }

  @override
  bool shouldRepaint(covariant MiniNetworkPainter oldDelegate) {
    return oldDelegate.facilities.length != facilities.length;
  }
}
