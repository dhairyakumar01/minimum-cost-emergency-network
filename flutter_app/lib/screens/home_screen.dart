import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'dashboard_screen.dart';
import 'facilities_screen.dart';
import 'mst_simulator_screen.dart';
import 'emergency_dispatch_screen.dart';
import 'results_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  void _onTabTapped(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      DashboardScreen(onNavigate: _onTabTapped),
      const FacilitiesScreen(),
      const MstSimulatorScreen(),
      const EmergencyDispatchScreen(),
      const ResultsScreen(),
    ];

    return LayoutBuilder(
      builder: (ctx, constraints) {
        final isWide = constraints.maxWidth >= 768;

        if (isWide) {
          return Scaffold(
            body: Row(
              children: [
                NavigationRail(
                  selectedIndex: _currentIndex,
                  onDestinationSelected: _onTabTapped,
                  backgroundColor: AppTheme.sidebarDark,
                  selectedIconTheme: const IconThemeData(color: Colors.white),
                  unselectedIconTheme: const IconThemeData(color: Colors.white70),
                  selectedLabelTextStyle: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                  unselectedLabelTextStyle: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                  leading: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Column(
                      children: [
                        Text('🚨', style: TextStyle(fontSize: 28)),
                        SizedBox(height: 6),
                        Text(
                          'BLR MST',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  destinations: const [
                    NavigationRailDestination(
                      icon: Icon(Icons.dashboard_outlined),
                      selectedIcon: Icon(Icons.dashboard),
                      label: Text('Dashboard'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.location_city_outlined),
                      selectedIcon: Icon(Icons.location_city),
                      label: Text('Facilities'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.hub_outlined),
                      selectedIcon: Icon(Icons.hub),
                      label: Text('MST Simulator'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.emergency_outlined),
                      selectedIcon: Icon(Icons.emergency),
                      label: Text('Dispatch'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.bar_chart_outlined),
                      selectedIcon: Icon(Icons.bar_chart),
                      label: Text('Results'),
                    ),
                  ],
                ),
                const VerticalDivider(width: 1, thickness: 1),
                Expanded(child: screens[_currentIndex]),
              ],
            ),
          );
        }

        // Mobile Layout: SafeArea wraps the screen body to prevent status bar and gesture navigation bar clipping
        return Scaffold(
          body: SafeArea(
            bottom: false,
            child: screens[_currentIndex],
          ),
          bottomNavigationBar: Container(
            decoration: const BoxDecoration(
              border: Border(
                top: BorderSide(color: AppTheme.borderLight, width: 1),
              ),
            ),
            child: BottomNavigationBar(
              currentIndex: _currentIndex,
              onTap: _onTabTapped,
              type: BottomNavigationBarType.fixed,
              backgroundColor: Colors.white,
              elevation: 4,
              selectedItemColor: AppTheme.sidebarDark,
              unselectedItemColor: AppTheme.textMuted,
              selectedFontSize: 11,
              unselectedFontSize: 11,
              selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w700),
              unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500),
              iconSize: 22,
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.dashboard_outlined),
                  activeIcon: Icon(Icons.dashboard),
                  label: 'Dashboard',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.location_city_outlined),
                  activeIcon: Icon(Icons.location_city),
                  label: 'Facilities',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.hub_outlined),
                  activeIcon: Icon(Icons.hub),
                  label: 'MST',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.emergency_outlined),
                  activeIcon: Icon(Icons.emergency),
                  label: 'Dispatch',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.bar_chart_outlined),
                  activeIcon: Icon(Icons.bar_chart),
                  label: 'Results',
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
