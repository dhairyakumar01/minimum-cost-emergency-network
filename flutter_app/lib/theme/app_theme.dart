import 'package:flutter/material.dart';

class AppTheme {
  // Brand & Core Colors
  static const Color primaryDark = Color(0xFF0F172A); // Slate navy
  static const Color sidebarDark = Color(0xFF064E3B); // Deep pine green
  static const Color accentNavy = Color(0xFF1E3A8A); // Kruskal dark navy
  static const Color accentEmerald = Color(0xFF059669); // Prim emerald
  static const Color accentAmber = Color(0xFFD97706); // Warning amber
  static const Color accentRed = Color(0xFFDC2626); // Emergency red
  static const Color bgCanvas = Color(0xFFF8FAFC); // Clean cool gray
  static const Color surfaceCard = Color(0xFFFFFFFF); // Pure white card
  static const Color borderLight = Color(0xFFE2E8F0); // Subtle card border
  static const Color textMain = Color(0xFF0F172A); // Primary high-contrast text
  static const Color textMuted = Color(0xFF64748B); // Secondary text
  static const Color textSubtle = Color(0xFF94A3B8); // Tertiary text

  // Agency Specific Identity Colors
  static const Color hospitalColor = Color(0xFFDC2626);
  static const Color policeColor = Color(0xFF2563EB);
  static const Color fireColor = Color(0xFFD97706);

  // Standard Spacing Scale
  static const double spaceXs = 4.0;
  static const double spaceSm = 8.0;
  static const double spaceMd = 12.0;
  static const double spaceLg = 16.0;
  static const double spaceXl = 20.0;

  // Standard Border Radii
  static final BorderRadius radiusCard = BorderRadius.circular(14.0);
  static final BorderRadius radiusButton = BorderRadius.circular(10.0);
  static final BorderRadius radiusBadge = BorderRadius.circular(6.0);
  static final BorderRadius radiusPill = BorderRadius.circular(20.0);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: sidebarDark,
        primary: sidebarDark,
        secondary: accentNavy,
        surface: surfaceCard,
        error: accentRed,
      ),
      scaffoldBackgroundColor: bgCanvas,
      appBarTheme: const AppBarTheme(
        backgroundColor: sidebarDark,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 16,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.2,
        ),
        iconTheme: IconThemeData(color: Colors.white, size: 20),
      ),
      cardTheme: CardThemeData(
        color: surfaceCard,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: borderLight, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: sidebarDark,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: sidebarDark,
          side: const BorderSide(color: borderLight, width: 1.2),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: sidebarDark, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        hintStyle: const TextStyle(color: textMuted, fontSize: 13),
        labelStyle: const TextStyle(color: textMuted, fontSize: 13),
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          visualDensity: VisualDensity.compact,
          textStyle: WidgetStateProperty.all(
            const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          ),
          shape: WidgetStateProperty.all(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        ),
      ),
    );
  }
}
