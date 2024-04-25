import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ayla',
      home: HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentIndex = 0;
  final List<String> _titles = const [
    'Início',
    'Perfil',
    'Configurações',
  ];

  List<Widget> _widgetOptions() {
    return [
          Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.start, 
      children: [
        // inserir imagem aqui
        Text(
          'Olá, Tyago',
          style: TextStyle(
            fontSize: 30,
            color: Colors.white,
          ),
        ),
        SizedBox(height: 20),
        Text(
          'Como posso te\najudar hoje?',
          style: TextStyle(
            color: Colors.white,
            fontSize: 24,
          ),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 50),
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.white,
              width: 2,
            ),
          ),
          child: IconButton(
            icon: const Icon(Icons.mic),
            iconSize: 60,
            color: Colors.white,
            onPressed: () {
            },
          ),
        ),
      ],
    ),
      Center(
        child: Text(
          'Você está na aba perfil', 
          style: TextStyle(
            fontSize: 24
          )
        )
      ),
      Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            'Teste', 
            style: TextStyle(fontSize: 24)
          ),
          ElevatedButton(
            onPressed: () {},
            child: Text('Sim'),
          ),
        ],
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_currentIndex]),
        centerTitle: true,
        backgroundColor: Color(0xFF0E1315),
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0), // Altura da borda
          child: Container(
            color: Color(0xFF0DAD9E), // Cor da borda
            height: 2.0, // Espessura da borda
          ),
        ),
      ),


      body: Center(
        child: _widgetOptions().elementAt(_currentIndex),
      ),
      backgroundColor: Color(0xFF0E1315),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(
            top: BorderSide(color: Color(0xFF0DAD9E), width: 2.0), // Cor e espessura da borda superior
          ),
        ),
        child: BottomNavigationBar(
          backgroundColor: Color(0xFF0E1315),
          onTap: (int newIndex) {
            setState(() {
              _currentIndex = newIndex;
            });
          },
          currentIndex: _currentIndex,
          items: const <BottomNavigationBarItem>[
            BottomNavigationBarItem(
              icon: Icon(Icons.home),
              label: 'Início',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person),
              label: 'Perfil',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.settings),
              label: 'Configurações',
            ),
          ],
          selectedItemColor: const Color(0xFF0DAD9E),
          unselectedItemColor: Colors.grey[600],
          showSelectedLabels: false,
          showUnselectedLabels: false,
        ),
      ),
    );
  }
}
