import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

void main() => runApp(const MyApp());

class RegistrationCompletePage extends StatelessWidget {
  const RegistrationCompletePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF0E1315),
        title: Text('Cadastro Concluído',
            style: GoogleFonts.josefinSans(color: Colors.white)),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Container(
              width: 1300,
              height: 100,
              child: Image.asset('assets/images/aylabrancoc.png'),
            ),
            Text(
              "Assistente Virtual",
              style: GoogleFonts.josefinSans(fontSize: 28, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 40),
            Text(
              "Obrigado por se cadastrar!",
              style: GoogleFonts.josefinSans(fontSize: 24, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 60),
            ElevatedButton(
              onPressed: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                foregroundColor: Colors.white,
                side: BorderSide(color: Colors.white, width: 2),
                elevation: 0,
                minimumSize: Size(200, 48),
              ),
              child: Text("Ir para o Login",
                  style: GoogleFonts.josefinSans(fontSize: 20)),
            ),
          ],
        ),
      ),
      backgroundColor: Color(0xFF0E1315),
    );
  }
}

class RegisterPage extends StatelessWidget {
  const RegisterPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF0E1315),
        title: Text('Cadastro',
            style: GoogleFonts.josefinSans(color: Colors.white)),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            children: <Widget>[
              Container(
                width: 1300,
                height: 100,
                child: Image.asset('assets/images/aylabrancoc.png'),
              ),
              Text(
                "Assistente Virtual",
                style:
                    GoogleFonts.josefinSans(fontSize: 28, color: Colors.white),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 20),
              TextField(
                cursorColor: Colors.white,
                decoration: InputDecoration(
                  labelText: 'Nome completo',
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 20),
              TextField(
                cursorColor: Colors.white,
                decoration: InputDecoration(
                  labelText: 'E-mail',
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 20),
              TextField(
                cursorColor: Colors.white,
                decoration: InputDecoration(
                  labelText: 'CEP',
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 20),
              TextField(
                cursorColor: Colors.white,
                obscureText: true, // Para entrada de senha
                decoration: InputDecoration(
                  labelText: 'Senha',
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 20),
              TextField(
                cursorColor: Colors.white,
                obscureText: true, // Para repetir a entrada da senha
                decoration: InputDecoration(
                  labelText: 'Repetir senha',
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 40),
              ElevatedButton(
                onPressed: () {
                  // Aqui você pode adicionar a lógica de validação do formulário antes de navegar
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const RegistrationCompletePage()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  side: BorderSide(color: Colors.white, width: 2),
                  elevation: 0,
                  minimumSize: Size(200, 48),
                ),
                child: Text('Registrar',
                    style: GoogleFonts.josefinSans(fontSize: 20)),
              )
            ],
          ),
        ),
      ),
      backgroundColor: Color(0xFF0E1315),
    );
  }
}

class ThankYouPage extends StatelessWidget {
  const ThankYouPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF0E1315),
        iconTheme: IconThemeData(color: Colors.white),
        title: Text("Obrigado",
            style: GoogleFonts.josefinSans(color: Colors.white)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment:
              MainAxisAlignment.start, // Alinha o conteúdo ao início
          children: <Widget>[
            SizedBox(
                height: MediaQuery.of(context).size.height *
                    0.1), // Reduzir este valor se necessário
            Container(
              width: 1300,
              height: 100,
              child: Image.asset('assets/images/aylabrancoc.png'),
            ),
            Text(
              "Assistente Virtual",
              style: GoogleFonts.josefinSans(fontSize: 28, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 40),
            Text(
              "Enviamos um link para\n seu E-mail.",
              style: GoogleFonts.josefinSans(fontSize: 24, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 60),
            ElevatedButton(
              onPressed: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                foregroundColor: Colors.white,
                side: BorderSide(color: Colors.white, width: 2),
                elevation: 0,
                minimumSize: Size(200, 48),
              ),
              child: Text("Retornar a tela de Login",
                  style: GoogleFonts.josefinSans(fontSize: 20)),
            ),
          ],
        ),
      ),
      backgroundColor: Color(0xFF0E1315),
    );
  }
}

class ForgotPasswordPage extends StatelessWidget {
  const ForgotPasswordPage({Key? key}) : super(key: key);

//Página 'Esqueci a Senha'

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        iconTheme: IconThemeData(color: Colors.white),
        title: Text("Recuperar Senha",
            style: GoogleFonts.josefinSans(color: Colors.white)),
        backgroundColor: Color(0xFF0E1315),
      ),
      body: SingleChildScrollView(
        // Permite rolagem quando o teclado aparece
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment:
                MainAxisAlignment.start, // Alinha o conteúdo ao topo
            children: <Widget>[
              Container(
                width: 1300, // Ajustado para ser mais realista
                height: 100,
                child: Image.asset('assets/images/aylabrancoc.png'),
              ),
              Text(
                "Assistente Virtual",
                style:
                    GoogleFonts.josefinSans(fontSize: 28, color: Colors.white),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 20),
              Text(
                "Digite seu e-mail para receber as instruções de recuperação de senha.",
                style:
                    GoogleFonts.josefinSans(fontSize: 18, color: Colors.white),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 20),
              TextField(
                keyboardType: TextInputType.emailAddress,
                cursorColor: Colors.white,
                decoration: InputDecoration(
                  labelText: "E-mail",
                  labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide:
                        BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                  ),
                ),
                style: TextStyle(color: Colors.white),
              ),
              SizedBox(height: 40),
              ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const ThankYouPage()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  side: BorderSide(color: Colors.white, width: 2),
                  elevation: 0,
                  minimumSize: Size(200, 48),
                ),
                child: Text("Avançar",
                    style: GoogleFonts.josefinSans(fontSize: 20)),
              ),
            ],
          ),
        ),
      ),
      backgroundColor: Color(0xFF0E1315),
    );
  }
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Login Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  bool _isPasswordVisible = false; // Controlar a visibilidade da senha

  @override
  Widget build(BuildContext context) {
    Color themeColor = Color(0xFF0DAD9E); // Definição da cor personalizada

    // Tela de login
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Container(
                width: 1300,
                height: 100,
                child: Image.asset('assets/images/aylabrancoc.png'),
              ),
              Text(
                "Assistente Virtual",
                style:
                    GoogleFonts.josefinSans(fontSize: 28, color: Colors.white),
              ),
              SizedBox(height: 20),
              TextField(
                controller: emailController,
                cursorColor: Colors.white, // Cor do cursor
                style: TextStyle(color: Colors.white), // Cor do texto digitado
                decoration: InputDecoration(
                  labelText: "E-mail",
                  labelStyle: TextStyle(color: themeColor),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor, width: 2.0),
                  ),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              SizedBox(height: 20),
              TextField(
                controller: passwordController,
                cursorColor: Colors.white, // Cor do cursor
                style: TextStyle(color: Colors.white), // Cor do texto digitado
                decoration: InputDecoration(
                  labelText: "Senha",
                  labelStyle: TextStyle(color: themeColor),
                  border: OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor, width: 2.0),
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _isPasswordVisible
                          ? Icons.visibility_off
                          : Icons.visibility,
                      color: Colors.white,
                    ),
                    onPressed: () {
                      setState(() {
                        _isPasswordVisible = !_isPasswordVisible;
                      });
                    },
                  ),
                ),
                obscureText: !_isPasswordVisible,
              ),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context) => const ForgotPasswordPage()),
                    );
                  },
                  child: Text(
                    'Esqueci a senha',
                    style: TextStyle(color: themeColor),
                  ),
                ),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const PerguntaApp()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  side: BorderSide(color: Colors.white, width: 2),
                  elevation: 0,
                  minimumSize: Size(200, 48),
                ),
                child:
                    Text("Login", style: GoogleFonts.josefinSans(fontSize: 20)),
              ),
              const SizedBox(height: 20),
              Row(
                children: <Widget>[
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(left: 10.0, right: 20.0),
                      child: Divider(
                        color: Color(0xFF0DAD9E),
                        height: 36,
                      ),
                    ),
                  ),
                  Text("Novo aqui?",
                      style: TextStyle(
                        color: Color(0xFF0DAD9E),
                        fontWeight: FontWeight.w600,
                      )),
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(left: 20.0, right: 10.0),
                      child: Divider(
                        color: Color(0xFF0DAD9E),
                        height: 36,
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const RegisterPage()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  side: BorderSide(color: Colors.white, width: 2),
                  elevation: 0,
                  minimumSize: Size(200, 48),
                ),
                child: Text("Cadastre-se",
                    style: GoogleFonts.josefinSans(fontSize: 20)),
              )
            ],
          ),
        ),
      ),
      backgroundColor: Color(0xFF0E1315), // Cor de fundo do Scaffold
    );
  }
}

class PerguntaApp extends StatefulWidget {
  const PerguntaApp({super.key});

  @override
  _PerguntaAppState createState() => _PerguntaAppState();
}

class _PerguntaAppState extends State<PerguntaApp> {
  int _currentIndex = 0;

  final List<String> _titles = const [
    'Início',
    'Perfil',
    'Configurações',
  ];

  // Tela principal
  List<Widget> current = [
    //Aba Início
    Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.start, // Alinhar conteúdo ao topo
      children: [
        Container(
          width:
              1300, // Verifique se esse tamanho é apropriado para a largura da tela
          height: 150, // Reduzido de 200 para 150
          child: Image.asset('assets/images/logomarcabranco.png'),
        ),
        SizedBox(height: 50), // Reduzido o espaço após a imagem
        Text(
          'Olá, Tyago',
          style: GoogleFonts.josefinSans(
            fontSize: 30,
            color: Colors.white,
          ),
        ),
        SizedBox(height: 20), // Reduzir ou ajustar conforme necessário
        Text(
          'Como posso te\najudar hoje?',
          style: GoogleFonts.josefinSans(
            color: Colors.white,
            fontSize: 24,
          ),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 50), // Espaçamento entre o texto e o botão
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.white, // Cor da borda do círculo
              width: 2, // Espessura da borda
            ),
          ),
          child: IconButton(
            icon: const Icon(Icons.mic),
            iconSize: 60, // Tamanho do ícone do microfone
            color: Colors.white, // Cor do ícone
            onPressed: () {
              // Implemente o que o botão deve fazer quando pressionado
            },
          ),
        ),
      ],
    ),

    // Aba Perfil
    Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.transparent,
              border: Border.all(color: Colors.white, width: 4),
            ),
            child: const Icon(Icons.person, size: 80, color: Colors.white), // Tamanho do ícone aumentado
          ),
          TextButton(
            onPressed: () {
                //route
            },
            style: TextButton.styleFrom(
              foregroundColor: Color(0xFF0DAD9E),
              textStyle: TextStyle(decoration: TextDecoration.underline),
            ),
            child: Text('Sair', style: TextStyle(color: Color(0xFF0DAD9E), fontSize: 16)),
          ),
          const SizedBox(height: 30),
          Text('Selecione a opção desejada:', style: GoogleFonts.josefinSans(fontSize: 22, color: Colors.white)),
          const SizedBox(height: 30),
          OutlinedButton(
            onPressed: () {},
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              backgroundColor: Color(0xFF0E1315), // Cor de fundo cinza escuro
              side: BorderSide(color: Colors.white, width: 2),
              textStyle: GoogleFonts.josefinSans(fontSize: 20),
              minimumSize: Size(240, 48),
            ),
            child: const Text('Editar foto de perfil'),
          ),
          // Continue adicionando outros botões de edição como "Editar nome", etc.
        ],
      ),
    //Aba Configurações
    Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 120, // Aumentado de 100 para 120
          height: 120, // Aumentado de 100 para 120
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.transparent,
            border: Border.all(
              color: Colors.white,
              width: 4,
            ),
          ),
          child: const Icon(Icons.settings,
              size: 80, color: Colors.white), // Tamanho do ícone aumentado
        ),
        const SizedBox(height: 60),
        Text(
          'Selecione a opção desejada:',
          style: GoogleFonts.josefinSans(
            fontSize: 22,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 30),
        OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Color(0xFF0E1315), // Cor de fundo cinza escuro
            side: BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: Size(240, 48),
          ),
          child: const Text('Reconfigurar sua voz'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Color(0xFF0E1315), // Cor de fundo cinza escuro
            side: BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: Size(240, 48),
          ),
          child: const Text('Alterar voz da Ayla'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Color(0xFF0E1315), // Cor de fundo cinza escuro
            side: BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: Size(240, 48),
          ),
          child: const Text('Alarmes e lembretes'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Color(0xFF0E1315), // Cor de fundo cinza escuro
            side: BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: Size(240, 48),
          ),
          child: const Text('Editar localização'),
        ),
      ],
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(kToolbarHeight),
          child: Container(
            decoration: const BoxDecoration(
              color: Color(0xFF0E1315),
              border: Border(
                bottom: BorderSide(
                  color: Color(0xFF0DAD9E),
                  width: 1.6,
                ),
              ),
            ),
            child: AppBar(
              title: Text(
                _titles[_currentIndex],
                style: GoogleFonts.josefinSans(
                  color: Colors.white,
                  fontSize: 28,
                ),
              ),
              backgroundColor: Colors.transparent,
              centerTitle: true,
              elevation: 0,
            ),
          ),
        ),
        backgroundColor: const Color(0xFF0E1315),
        body: Center(
          child: current[_currentIndex],
        ),
        bottomNavigationBar: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              top: BorderSide(color: Color(0xFF0DAD9E), width: 1.5),
            ),
          ),
          child: BottomNavigationBar(
            iconSize: 40,
            backgroundColor: const Color(0xFF0E1315),
            currentIndex: _currentIndex,
            onTap: (int newIndex) {
              setState(() {
                _currentIndex = newIndex;
              });
            },
            items: const [
              BottomNavigationBarItem(
                label: 'Início',
                icon: Icon(Icons.home),
              ),
              BottomNavigationBarItem(
                label: 'Perfil',
                icon: Icon(Icons.person),
              ),
              BottomNavigationBarItem(
                label: 'Configurações',
                icon: Icon(Icons.settings),
              ),
            ],
            selectedItemColor: const Color(0xFF0DAD9E),
            unselectedItemColor: Colors.grey[600],
            showSelectedLabels: false,
            showUnselectedLabels: false,
          ),
        ),
      ),
    );
  }
}
