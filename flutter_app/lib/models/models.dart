class Facility {
  final String id;
  final String name;
  final String agency;
  final double latitude;
  final double longitude;
  final String? address;

  Facility({
    required this.id,
    required this.name,
    required this.agency,
    required this.latitude,
    required this.longitude,
    this.address,
  });

  factory Facility.fromJson(Map<String, dynamic> json) {
    return Facility(
      id: json['facility_id'] ?? json['id'] ?? '',
      name: json['facility_name'] ?? json['name'] ?? 'Facility',
      agency: json['agency'] ?? 'hospital',
      latitude: (json['latitude'] ?? json['lat'] ?? 0.0).toDouble(),
      longitude: (json['longitude'] ?? json['lon'] ?? 0.0).toDouble(),
      address: json['address'],
    );
  }
}

class MstTraceEvent {
  final int sequenceNumber;
  final String eventType;
  final String action;
  final bool accepted;
  final String? sourceVertexId;
  final String? targetVertexId;
  final String? sourceName;
  final String? targetName;
  final double? uLat;
  final double? uLon;
  final double? vLat;
  final double? vLon;
  final String edgeWeightFormatted;
  final String currentTreeWeightFormatted;
  final int acceptedEdgeCount;
  final int totalRequiredEdges;
  final int remainingEdgeCount;
  final int? componentCount;
  final int? visitedVertexCount;
  final String? decisionRationale;

  MstTraceEvent({
    required this.sequenceNumber,
    required this.eventType,
    required this.action,
    required this.accepted,
    this.sourceVertexId,
    this.targetVertexId,
    this.sourceName,
    this.targetName,
    this.uLat,
    this.uLon,
    this.vLat,
    this.vLon,
    required this.edgeWeightFormatted,
    required this.currentTreeWeightFormatted,
    required this.acceptedEdgeCount,
    required this.totalRequiredEdges,
    required this.remainingEdgeCount,
    this.componentCount,
    this.visitedVertexCount,
    this.decisionRationale,
  });

  factory MstTraceEvent.fromJson(Map<String, dynamic> json) {
    final uCoords = json['u_coords'] as List<dynamic>?;
    final vCoords = json['v_coords'] as List<dynamic>?;

    return MstTraceEvent(
      sequenceNumber: json['sequence_number'] ?? 0,
      eventType: json['event_type'] ?? 'EVALUATED',
      action: json['action'] ?? '',
      accepted: json['accepted'] == true || json['event_type'] == 'EDGE_ACCEPTED',
      sourceVertexId: json['source_vertex_id'] ?? json['u'],
      targetVertexId: json['target_vertex_id'] ?? json['v'],
      sourceName: json['source_name'] ?? json['u_name'] ?? json['u'],
      targetName: json['target_name'] ?? json['v_name'] ?? json['v'],
      uLat: (json['u_lat'] ?? (uCoords != null && uCoords.isNotEmpty ? uCoords[0] : null))?.toDouble(),
      uLon: (json['u_lon'] ?? (uCoords != null && uCoords.length > 1 ? uCoords[1] : null))?.toDouble(),
      vLat: (json['v_lat'] ?? (vCoords != null && vCoords.isNotEmpty ? vCoords[0] : null))?.toDouble(),
      vLon: (json['v_lon'] ?? (vCoords != null && vCoords.length > 1 ? vCoords[1] : null))?.toDouble(),
      edgeWeightFormatted: json['edge_weight_formatted'] ?? '0.000 km',
      currentTreeWeightFormatted: json['current_tree_weight_formatted'] ?? '0.000 km',
      acceptedEdgeCount: json['accepted_edge_count'] ?? json['step'] ?? 0,
      totalRequiredEdges: json['total_required_edges'] ?? 0,
      remainingEdgeCount: json['remaining_edge_count'] ?? 0,
      componentCount: json['component_count'],
      visitedVertexCount: json['visited_vertex_count'],
      decisionRationale: json['decision_rationale'] ?? json['reason'],
    );
  }
}

class SystemHealth {
  final bool isHealthy;
  final int facilitiesCount;
  final int globalMstEdges;
  final String statusText;

  SystemHealth({
    required this.isHealthy,
    required this.facilitiesCount,
    required this.globalMstEdges,
    required this.statusText,
  });
}
