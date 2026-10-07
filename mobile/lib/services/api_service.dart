import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../core/config.dart';
import '../models/analysis_result.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ServerHealth {
  const ServerHealth({required this.status, required this.modelLoaded, required this.demoMode, this.modelVersion, this.detail});

  factory ServerHealth.fromJson(Map<String, dynamic> json) => ServerHealth(
        status: json['status'] as String? ?? 'unknown',
        modelLoaded: json['model_loaded'] as bool? ?? false,
        demoMode: json['demo_mode'] as bool? ?? false,
        modelVersion: json['model_version'] as String?,
        detail: json['detail'] as String?,
      );

  final String status;
  final bool modelLoaded;
  final bool demoMode;
  final String? modelVersion;
  final String? detail;
}

/// Client for the Glowrithm FastAPI backend (backend/app/main.py).
class ApiService {
  ApiService(String baseUrl) : baseUrl = baseUrl.trim().replaceAll(RegExp(r'/+$'), '');

  final String baseUrl;

  Map<String, String> get _headers => {
        'Accept': 'application/json',
        if (AppConfig.apiKey.isNotEmpty) 'X-API-Key': AppConfig.apiKey,
      };

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<ServerHealth> health() async {
    final response = await _guard(
      () => http.get(_uri('/api/v1/health'), headers: _headers).timeout(const Duration(seconds: 10)),
    );
    return ServerHealth.fromJson(_decode(response));
  }

  /// Uploads one photo with the profile data and explicit consent; returns the full analysis.
  Future<AnalysisResult> analyze({required String imagePath, required int age, required String sex}) async {
    final response = await _guard(() async {
      final request = http.MultipartRequest('POST', _uri('/api/v1/analyze'))
        ..headers.addAll(_headers)
        ..fields['consent'] = 'true'
        ..fields['age'] = '$age'
        ..fields['sex'] = sex
        ..files.add(await http.MultipartFile.fromPath('image', imagePath));
      final streamed = await request.send().timeout(AppConfig.requestTimeout);
      return http.Response.fromStream(streamed).timeout(AppConfig.requestTimeout);
    });
    return AnalysisResult.fromJson(_decode(response));
  }

  /// Turns low-level network failures into messages a user can act on.
  Future<http.Response> _guard(Future<http.Response> Function() call) async {
    try {
      return await call();
    } on TimeoutException {
      throw ApiException('The server took too long to respond. Check your connection and try again.');
    } on SocketException {
      throw ApiException('Cannot reach the server at $baseUrl. Check the address in Profile > Server settings.');
    } on HandshakeException {
      throw ApiException('The secure connection failed. Check that the server has a valid HTTPS certificate.');
    } on http.ClientException catch (error) {
      throw ApiException('Connection error: ${error.message}');
    } on FormatException {
      throw ApiException('The server address is not valid: $baseUrl');
    } on ArgumentError {
      throw ApiException('The server address is not valid: $baseUrl');
    }
  }

  Map<String, dynamic> _decode(http.Response response) {
    Object? body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      body = null;
    }
    final ok = response.statusCode >= 200 && response.statusCode < 300;
    if (ok && body is Map<String, dynamic>) return body;
    final detail = body is Map<String, dynamic> ? body['detail'] : null;
    throw ApiException(
      detail is String ? detail : 'The server returned an error (HTTP ${response.statusCode}).',
      statusCode: response.statusCode,
    );
  }
}
