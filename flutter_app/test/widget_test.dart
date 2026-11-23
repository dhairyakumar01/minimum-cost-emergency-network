import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:emergency_network_app/main.dart';

void main() {
  testWidgets('App renders successfully smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const EmergencyNetworkApp());
    expect(find.text('Bengaluru MST Network'), findsOneWidget);
  });

  testWidgets('Mobile screen 360x640 layout and navigation test with 0 overflows', (WidgetTester tester) async {
    // Compact phone screen dimension (360x640 dp)
    tester.view.physicalSize = const Size(360, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const EmergencyNetworkApp());
    await tester.pumpAndSettle();

    // Check dashboard elements
    expect(find.text('Bengaluru MST Network'), findsOneWidget);
    expect(find.text('Platform Overview'), findsOneWidget);
    expect(find.text('Total Facilities'), findsOneWidget);
    expect(find.text('Spanning Links'), findsOneWidget);

    // Switch to Facilities tab
    await tester.tap(find.text('Facilities'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Facilities Map'), findsOneWidget);
    expect(find.text('Map View'), findsOneWidget);
    expect(find.text('List View'), findsOneWidget);

    // Switch to MST Simulator tab
    await tester.tap(find.text('MST'));
    await tester.pumpAndSettle();
    expect(find.text('MST Network Simulator'), findsOneWidget);
    expect(find.text("Kruskal's Algorithm"), findsOneWidget);
    expect(find.text("Prim's Algorithm"), findsOneWidget);

    // Switch to Dispatch tab
    await tester.tap(find.text('Dispatch'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Simulation & Dispatch'), findsOneWidget);
    expect(find.text('Incident Location & Landmark'), findsOneWidget);

    // Switch to Results tab
    await tester.tap(find.text('Results'));
    await tester.pumpAndSettle();
    expect(find.text('Results & Statistics'), findsOneWidget);
    expect(find.text('Algorithmic Parity Confirmed'), findsOneWidget);
  });

  testWidgets('Mobile screen 390x844 layout test with 0 overflows', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const EmergencyNetworkApp());
    await tester.pumpAndSettle();

    expect(find.text('Bengaluru MST Network'), findsOneWidget);
    expect(find.text('Total Facilities'), findsOneWidget);
    expect(find.text('Parity Verified'), findsOneWidget);

    // Tap through all tabs to verify no overflows on 390x844
    await tester.tap(find.text('Facilities'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Facilities Map'), findsOneWidget);

    await tester.tap(find.text('MST'));
    await tester.pumpAndSettle();
    expect(find.text('MST Network Simulator'), findsOneWidget);

    await tester.tap(find.text('Dispatch'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Simulation & Dispatch'), findsOneWidget);

    await tester.tap(find.text('Results'));
    await tester.pumpAndSettle();
    expect(find.text('Results & Statistics'), findsOneWidget);
  });

  testWidgets('Mobile screen 412x915 layout test with 0 overflows', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(412, 915);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const EmergencyNetworkApp());
    await tester.pumpAndSettle();

    expect(find.text('Bengaluru MST Network'), findsOneWidget);
    expect(find.text('Total Facilities'), findsOneWidget);

    // Verify Facilities View toggle
    await tester.tap(find.text('Facilities'));
    await tester.pumpAndSettle();
    expect(find.text('Map View'), findsOneWidget);
    // Tap List View toggle
    await tester.tap(find.text('List View'));
    await tester.pumpAndSettle();

    // Verify MST controls
    await tester.tap(find.text('MST'));
    await tester.pumpAndSettle();
    expect(find.text('Graph Scope:'), findsOneWidget);

    // Verify Dispatch
    await tester.tap(find.text('Dispatch'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Simulation & Dispatch'), findsOneWidget);

    // Verify Results
    await tester.tap(find.text('Results'));
    await tester.pumpAndSettle();
    expect(find.text('Algorithmic Parity Confirmed'), findsOneWidget);
  });
}
