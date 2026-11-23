import 'package:flutter_test/flutter_test.dart';
import 'package:emergency_network_app/main.dart';

void main() {
  testWidgets('App renders successfully smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const EmergencyNetworkApp());
    expect(find.text('Bengaluru MST Network'), findsOneWidget);
  });
}
