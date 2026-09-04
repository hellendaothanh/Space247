import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const ProviderScope(
      child: Space247App(),
    ),
  );
}

class Space247App extends StatelessWidget {
  const Space247App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Space247',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
    );
  }
}
