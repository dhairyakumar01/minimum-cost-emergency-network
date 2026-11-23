import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  static const String productionUrl = 'https://minimum-cost-emergency-network.vercel.app';

  static String _resolveDefaultBaseUrl() {
    if (kIsWeb) {
      final origin = Uri.base.origin;
      if (origin.isNotEmpty && !origin.startsWith('file:') && !origin.contains('localhost:0')) {
        return origin;
      }
      return 'http://127.0.0.1:5000';
    }
    // On Android / mobile, communicate with the production Vercel cloud backend
    return productionUrl;
  }

  static String baseUrl = _resolveDefaultBaseUrl();

  static void setBaseUrl(String url) {
    baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  static Future<SystemHealth> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/health'))
          .timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final stats = data['stats'] ?? data['data'] ?? {};
        return SystemHealth(
          isHealthy: true,
          facilitiesCount: stats['facilities_count'] ?? 1255,
          globalMstEdges: stats['global_mst_edges'] ?? 1254,
          statusText: 'System Operational (200 OK)',
        );
      }
      return SystemHealth(
        isHealthy: false,
        facilitiesCount: 0,
        globalMstEdges: 0,
        statusText: 'Server Error (${response.statusCode})',
      );
    } catch (e) {
      return SystemHealth(
        isHealthy: false,
        facilitiesCount: 1255,
        globalMstEdges: 1254,
        statusText: 'Offline / Connecting: $e',
      );
    }
  }

  static Future<List<Facility>> getFacilities({
    String? agency,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (agency != null && agency.isNotEmpty && agency != 'all') {
        queryParams['agency'] = agency;
      }
      if (search != null && search.isNotEmpty) {
        queryParams['search'] = search;
      }

      final uri = Uri.parse('$baseUrl/api/facilities').replace(
        queryParameters: queryParams.isEmpty ? null : queryParams,
      );

      final response = await http.get(uri).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        final List<dynamic> list = body['data'] ?? body['facilities'] ?? [];
        return list.map((item) => Facility.fromJson(item)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  static Future<Map<String, dynamic>> getMstTrace({
    String graph = 'global',
    String algo = 'kruskal',
    double? lat,
    double? lon,
    double? radiusKm,
  }) async {
    final queryParams = <String, String>{
      'graph': graph,
      'algo': algo,
    };
    if (lat != null && lon != null) {
      queryParams['lat'] = lat.toString();
      queryParams['lon'] = lon.toString();
      queryParams['radius_km'] = (radiusKm ?? 5.0).toString();
    }

    final uri = Uri.parse('$baseUrl/api/mst/trace').replace(
      queryParameters: queryParams,
    );

    final response = await http.get(uri).timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body);
      return body['data'] ?? body;
    } else {
      throw Exception('Failed to load trace: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> runScenario({
    required double lat,
    required double lon,
    required String label,
    required String category,
    required String agency,
    required String mode,
    required int kParam,
  }) async {
    final payload = {
      'incident': {
        'latitude': lat,
        'longitude': lon,
        'label': label,
      },
      'category': category,
      'agency': agency,
      'mode': mode,
      'k_param': kParam,
    };

    final uri = Uri.parse('$baseUrl/api/scenarios');
    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 20));

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to run dispatch scenario: ${response.statusCode}');
    }
  }
}

