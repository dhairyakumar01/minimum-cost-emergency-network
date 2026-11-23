import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class EmergencyDispatchScreen extends StatefulWidget {
  const EmergencyDispatchScreen({super.key});

  @override
  State<EmergencyDispatchScreen> createState() => _EmergencyDispatchScreenState();
}

class _EmergencyDispatchScreenState extends State<EmergencyDispatchScreen> {
  final _latController = TextEditingController(text: '12.9781');
  final _lonController = TextEditingController(text: '77.5696');
  final _labelController = TextEditingController(text: 'Majestic (KSR Railway Station)');

  String _category = 'medical';
  String _agency = 'hospital';
  String _mode = 'time';
  final int _kParam = 5;

  bool _loading = false;
  Map<String, dynamic>? _scenarioResult;

  Future<void> _runDispatch() async {
    final lat = double.tryParse(_latController.text.trim()) ?? 12.9781;
    final lon = double.tryParse(_lonController.text.trim()) ?? 77.5696;

    setState(() => _loading = true);

    try {
      final res = await ApiService.runScenario(
        lat: lat,
        lon: lon,
        label: _labelController.text.trim(),
        category: _category,
        agency: _agency,
        mode: _mode,
        kParam: _kParam,
      );

      if (mounted) {
        setState(() {
          _scenarioResult = res['data'] ?? res;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Dispatch Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ranking = (_scenarioResult?['dispatch_ranking'] as List<dynamic>? ?? []);
    final topFacility = ranking.isNotEmpty ? ranking[0] : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Simulation & Dispatch', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Workflow Configuration Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Incident & Dispatch Setup',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 12),

                    // Incident Label
                    TextField(
                      controller: _labelController,
                      decoration: const InputDecoration(
                        labelText: 'Incident Location / Landmark',
                        prefixIcon: Icon(Icons.location_on),
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Coordinates Row
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _latController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: 'Latitude (°N)'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            controller: _lonController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: 'Longitude (°E)'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Category Selector
                    const Text('Emergency Category:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      children: [
                        _categoryChip('Medical (Hospital)', 'medical', 'hospital', Icons.local_hospital),
                        _categoryChip('Fire & Rescue', 'fire', 'fire', Icons.local_fire_department),
                        _categoryChip('Police / Law', 'security', 'police', Icons.local_police),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Optimization Mode
                    const Text('Routing Optimization Mode:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      initialValue: _mode,
                      decoration: const InputDecoration(isDense: true),
                      items: const [
                        DropdownMenuItem(value: 'time', child: Text('Mode 1: Minimum Time (Fastest Dispatch)')),
                        DropdownMenuItem(value: 'distance', child: Text('Mode 2: Minimum Road Distance (Shortest Path)')),
                        DropdownMenuItem(value: 'compromise', child: Text('Mode 3: Risk-Balanced Compromise (Weighted Score)')),
                      ],
                      onChanged: (val) {
                        if (val != null) setState(() => _mode = val);
                      },
                    ),
                    const SizedBox(height: 16),

                    // Run Dispatch Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _loading ? null : _runDispatch,
                        icon: _loading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                              )
                            : const Icon(Icons.flash_on),
                        label: Text(_loading ? 'Computing Optimal Dispatch...' : 'Run Emergency Dispatch Simulation'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.accentRed,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Results Section
            if (topFacility != null) ...[
              const Text(
                'Optimal Dispatch Recommendation',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),

              // Top #1 Recommended Card
              Card(
                color: const Color(0xFFFFFBEB),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: Color(0xFFFDE68A), width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppTheme.accentAmber,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Text(
                              '⭐ #1 RECOMMENDED DISPATCH FACILITY',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                            ),
                          ),
                          Text(
                            topFacility['agency']?.toString().toUpperCase() ?? 'EMERGENCY',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppTheme.textMuted),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(
                        topFacility['facility_name'] ?? 'Facility',
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textMain),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'ID: ${topFacility['facility_id']}',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontFamily: 'monospace'),
                      ),
                      const Divider(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _statItem(
                            'EST. TRAVEL TIME',
                            '${(topFacility['travel_time_min'] ?? (topFacility['travel_time_ds'] != null ? topFacility['travel_time_ds'] / 600.0 : 0.0)).toStringAsFixed(1)} min',
                            AppTheme.accentRed,
                          ),
                          _statItem(
                            'ROAD DISTANCE',
                            '${(topFacility['road_distance_km'] ?? (topFacility['road_distance_dm'] != null ? topFacility['road_distance_dm'] / 10000.0 : 0.0)).toStringAsFixed(2)} km',
                            AppTheme.accentNavy,
                          ),
                          _statItem(
                            'DISPATCH SCORE',
                            '${topFacility['compromise_score'] ?? topFacility['weight'] ?? 100}',
                            AppTheme.sidebarDark,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Alternative Ranked Facilities
              const Text(
                'Alternative Standby Stations (Rank #2 - #5)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 8),

              ...ranking.skip(1).take(4).toList().asMap().entries.map((entry) {
                final idx = entry.key + 2;
                final f = entry.value;
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: Colors.blue.withAlpha(30),
                      child: Text(
                        '#$idx',
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
                      ),
                    ),
                    title: Text(
                      f['facility_name'] ?? 'Alternative Facility',
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    subtitle: Text(
                      'Travel: ${(f['travel_time_min'] ?? 0.0).toStringAsFixed(1)} min • Dist: ${(f['road_distance_km'] ?? 0.0).toStringAsFixed(2)} km',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _categoryChip(String label, String cat, String agency, IconData icon) {
    final selected = _category == cat;
    return ChoiceChip(
      avatar: Icon(icon, size: 16, color: selected ? Colors.white : AppTheme.sidebarDark),
      label: Text(label),
      selected: selected,
      selectedColor: AppTheme.sidebarDark,
      labelStyle: TextStyle(
        color: selected ? Colors.white : AppTheme.textMain,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        fontSize: 12,
      ),
      onSelected: (_) {
        setState(() {
          _category = cat;
          _agency = agency;
        });
      },
    );
  }

  Widget _statItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}
