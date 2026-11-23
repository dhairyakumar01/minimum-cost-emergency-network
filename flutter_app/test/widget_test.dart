import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:emergency_network_app/main.dart';

void main() {
  testWidgets('App renders successfully smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const EmergencyNetworkApp());
    expect(find.text('Bengaluru MST Network'), findsOneWidget);
  });

  testWidgets('Mobile screen 360x640 layout and navigation test with 0 overflows', (WidgetTester tester) async {
    // Set compact phone screen dimension (360x640 dp)
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
    expect(find.text('Facilities Directory'), findsOneWidget);

    // Switch to MST Simulator tab
    await tester.tap(find.text('MST'));
    await tester.pumpAndSettle();
    expect(find.text('MST Construction Simulator'), findsOneWidget);

    // Switch to Dispatch tab
    await tester.tap(find.text('Dispatch'));
    await tester.pumpAndSettle();
    expect(find.text('Emergency Simulation & Dispatch'), findsOneWidget);

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
  });
}
