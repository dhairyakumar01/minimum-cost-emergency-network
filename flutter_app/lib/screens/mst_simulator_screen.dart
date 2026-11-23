import 'dart:async';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class MstSimulatorScreen extends StatefulWidget {
  const MstSimulatorScreen({super.key});

  @override
  State<MstSimulatorScreen> createState() => _MstSimulatorScreenState();
}

class _MstSimulatorScreenState extends State<MstSimulatorScreen> {
  String _graphContext = 'global';
  String _algorithm = 'kruskal';

  List<MstTraceEvent> _events = [];
  int _currentStep = 0;
  bool _loading = false;
  bool _isPlaying = false;
  Timer? _playbackTimer;

  final double _incidentLat = 12.9781;
  final double _incidentLon = 77.5696;
  int _coveredFacilityCount = 400;

  @override
  void initState() {
    super.initState();
    _loadTrace();
  }

  @override
  void dispose() {
    _playbackTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadTrace() async {
    _pause();
    setState(() => _loading = true);

    try {
      final res = await ApiService.getMstTrace(
        graph: _graphContext,
        algo: _algorithm,
        lat: _graphContext == 'incident' ? _incidentLat : null,
        lon: _graphContext == 'incident' ? _incidentLon : null,
        radiusKm: 5.0,
      );

      final rawEvents = (res['events'] as List<dynamic>? ?? []);
      final parsed = rawEvents.map((e) => MstTraceEvent.fromJson(e)).toList();

      final vertices = (res['vertices'] as List<dynamic>? ?? []);

      if (mounted) {
        setState(() {
          _events = parsed;
          _currentStep = 0;
          _coveredFacilityCount = vertices.isNotEmpty ? vertices.length - 1 : 400;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load algorithm trace: $e')),
        );
      }
    }
  }

  void _play() {
    if (_events.isEmpty) return;
    setState(() => _isPlaying = true);
    _playbackTimer = Timer.periodic(const Duration(milliseconds: 150), (timer) {
      if (_currentStep < _events.length - 1) {
        setState(() => _currentStep++);
      } else {
        _pause();
      }
    });
  }

  void _pause() {
    _playbackTimer?.cancel();
    if (mounted) setState(() => _isPlaying = false);
  }

  void _restart() {
    _pause();
    setState(() => _currentStep = 0);
  }

  void _next() {
    _pause();
    if (_currentStep < _events.length - 1) {
      setState(() => _currentStep++);
    }
  }

  void _prev() {
    _pause();
    if (_currentStep > 0) {
      setState(() => _currentStep--);
    }
  }

  @override
  Widget build(BuildContext context) {
    final curEv = _events.isNotEmpty && _currentStep < _events.length
        ? _events[_currentStep]
        : null;

    final acceptedCount = curEv?.acceptedEdgeCount ?? 0;
    final totalEdges = curEv?.totalRequiredEdges ?? (_events.isNotEmpty ? _events.last.totalRequiredEdges : 1254);
    final weightStr = curEv?.currentTreeWeightFormatted ?? '0.000 km';
    final stateStr = curEv?.eventType ?? 'START';

    return Scaffold(
      appBar: AppBar(
        title: const Text('MST Construction Simulator', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Controls Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: [
                    // Toggles Row
                    Wrap(
                      spacing: 12,
                      runSpacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        // Graph Context
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('Graph: ', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            SegmentedButton<String>(
                              segments: const [
                                ButtonSegment(value: 'global', label: Text('Global (1,255)')),
                                ButtonSegment(value: 'incident', label: Text('5km Incident')),
                              ],
                              selected: {_graphContext},
                              onSelectionChanged: (val) {
                                setState(() => _graphContext = val.first);
                                _loadTrace();
                              },
                            ),
                          ],
                        ),
                        // Algorithm
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('Algo: ', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            SegmentedButton<String>(
                              segments: const [
                                ButtonSegment(value: 'kruskal', label: Text('Kruskal')),
                                ButtonSegment(value: 'prim', label: Text('Prim')),
                              ],
                              selected: {_algorithm},
                              onSelectionChanged: (val) {
                                setState(() => _algorithm = val.first);
                                _loadTrace();
                              },
                            ),
                          ],
                        ),
                      ],
                    ),

                    if (_graphContext == 'incident') ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFEFF6FF),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFFBFDBFE)),
                        ),
                        child: Row(
                          children: [
                            const Text('🚨', style: TextStyle(fontSize: 16)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '5.0 km Incident Graph: ${_incidentLat.toStringAsFixed(4)}°N, ${_incidentLon.toStringAsFixed(4)}°E • $_coveredFacilityCount facilities',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF1E3A8A)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 12),

                    // Playback Controls
                    Row(
                      children: [
                        IconButton(
                          onPressed: _restart,
                          icon: const Icon(Icons.replay),
                          tooltip: 'Restart',
                        ),
                        IconButton(
                          onPressed: _prev,
                          icon: const Icon(Icons.skip_previous),
                          tooltip: 'Previous Step',
                        ),
                        ElevatedButton.icon(
                          onPressed: _isPlaying ? _pause : _play,
                          icon: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
                          label: Text(_isPlaying ? 'Pause' : 'Play'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _algorithm == 'prim' ? AppTheme.accentEmerald : AppTheme.accentNavy,
                          ),
                        ),
                        IconButton(
                          onPressed: _next,
                          icon: const Icon(Icons.skip_next),
                          tooltip: 'Next Step',
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Event $_currentStep of ${_events.length}',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),

                    // Scrubber Slider
                    Slider(
                      value: _events.isNotEmpty ? _currentStep.clamp(0, _events.length - 1).toDouble() : 0.0,
                      min: 0.0,
                      max: _events.isNotEmpty ? (_events.length - 1).toDouble() : 1.0,
                      divisions: _events.isNotEmpty ? _events.length : 1,
                      activeColor: _algorithm == 'prim' ? AppTheme.accentEmerald : AppTheme.accentNavy,
                      onChanged: (val) {
                        _pause();
                        setState(() => _currentStep = val.toInt());
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Live Telemetry Strip
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _telemItem('STATE', stateStr, Colors.blue),
                    _telemItem('TREE WEIGHT', weightStr, AppTheme.accentAmber),
                    _telemItem('ACCEPTED EDGES', '$acceptedCount / $totalEdges', AppTheme.sidebarDark),
                    _telemItem(
                      _algorithm == 'kruskal' ? 'COMPONENTS' : 'VISITED CUT',
                      '${_algorithm == 'kruskal' ? (curEv?.componentCount ?? 0) : (curEv?.visitedVertexCount ?? 0)}',
                      Colors.purple,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Visual Canvas (Cleaner edge rendering without dots)
            Container(
              height: 260,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Stack(
                  children: [
                    CustomPaint(
                      size: const Size(double.infinity, 260),
                      painter: MstGraphPainter(
                        events: _events,
                        currentStep: _currentStep,
                        algo: _algorithm,
                      ),
                    ),
                    if (_loading)
                      const Center(child: CircularProgressIndicator(color: Colors.white)),
                    Positioned(
                      bottom: 8,
                      left: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.black.withAlpha(180),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          '${_algorithm.toUpperCase()} SPANNING TREE • $acceptedCount EDGES ACCEPTED',
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontFamily: 'monospace'),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Step Explanation Panel
            if (curEv != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Step #${curEv.sequenceNumber} (${curEv.eventType})',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: curEv.accepted ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              curEv.accepted ? 'ACCEPTED' : (curEv.eventType == 'EDGE_REJECTED' ? 'CYCLE REJECTED' : 'INFO'),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: curEv.accepted ? const Color(0xFF166534) : const Color(0xFF991B1B),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Edge: ${curEv.sourceName ?? curEv.sourceVertexId ?? "Root"} ↔ ${curEv.targetName ?? curEv.targetVertexId ?? "—"}',
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                      Text(
                        'Weight: ${curEv.edgeWeightFormatted}',
                        style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                      ),
                      if (curEv.decisionRationale != null && curEv.decisionRationale!.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: AppTheme.bgCanvas,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            curEv.decisionRationale!,
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMain),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _telemItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}

class MstGraphPainter extends CustomPainter {
  final List<MstTraceEvent> events;
  final int currentStep;
  final String algo;

  MstGraphPainter({
    required this.events,
    required this.currentStep,
    required this.algo,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (events.isEmpty) return;

    // Fixed geographic bounding box for Bengaluru
    const minLat = 12.80;
    const maxLat = 13.15;
    const minLon = 77.40;
    const maxLon = 77.80;

    double projectX(double lon) => ((lon - minLon) / (maxLon - minLon)) * size.width;
    double projectY(double lat) => size.height - (((lat - minLat) / (maxLat - minLat)) * size.height);

    final edgePaint = Paint()
      ..color = algo == 'prim' ? const Color(0xFF10B981) : const Color(0xFF3B82F6)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final evalPaint = Paint()
      ..color = const Color(0xFFF59E0B)
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;

    // Draw all accepted edges up to currentStep
    for (int i = 0; i <= currentStep && i < events.length; i++) {
      final ev = events[i];
      if (ev.accepted && ev.uLat != null && ev.uLon != null && ev.vLat != null && ev.vLon != null) {
        final x1 = projectX(ev.uLon!);
        final y1 = projectY(ev.uLat!);
        final x2 = projectX(ev.vLon!);
        final y2 = projectY(ev.vLat!);

        final isCurrent = i == currentStep;
        canvas.drawLine(
          Offset(x1, y1),
          Offset(x2, y2),
          isCurrent ? evalPaint : edgePaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant MstGraphPainter oldDelegate) {
    return oldDelegate.currentStep != currentStep || oldDelegate.algo != algo;
  }
}
