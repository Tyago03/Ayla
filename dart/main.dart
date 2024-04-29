import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:google_maps_flutter/google_maps_flutter.dart';

//Cores principais usadas:
// Plano de fundo: #0E1315
// Cor dos realces: #0DAD9E

void main() => runApp(const MyApp());

// Variável global da NavBar
int currentIndex = 0;

//Lista armazenar alarmes
List<String> alarmes = [];

class PerguntaApp extends StatefulWidget {
  const PerguntaApp({super.key});

  @override
  _PerguntaAppState createState() => _PerguntaAppState();
}

class _PerguntaAppState extends State<PerguntaApp> {
  //Variável salvar horário selecionado
  TimeOfDay selectedTime = TimeOfDay(hour: 0, minute: 0);

  // Função para selecionar tempo
  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: selectedTime,
    );
    if (picked != null && picked != selectedTime) {
      setState(() {
        selectedTime = picked; // Agora usando setState corretamente
      });
    }
  }

  //Nome do usuário
  String nomeUsuario = 'User';

  // Variável para armazenar a imagem selecionada
  XFile? _imageFile;

  // Método para alterar o nome do usuário
  void _alterarNomeUsuario(String novoNome) {
    setState(() {
      nomeUsuario = novoNome.isNotEmpty ? novoNome : 'User';
    });
  }

  // Função para pegar a imagem da galeria ou câmera
  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await ImagePicker().pickImage(source: source);
      if (pickedFile != null) {
        setState(() {
          _imageFile = pickedFile;
        });
      }
    } catch (e) {
      // Lidar com exceções
      print('Erro ao pegar a imagem: $e');
    }
  }

  // Widget para mostrar a imagem selecionada ou o ícone padrão
  Widget _buildImage() {
    if (_imageFile == null) {
      return Icon(Icons.person, size: 120, color: Colors.white);
    } else {
      return Container(
        width: 180,
        height: 180,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: Color(0xFF0DAD9E), // Cor dos realces
            width: 4, // Espessura da borda
          ),
        ),
        child: ClipOval(
          child: Image.file(
            File(_imageFile!.path),
            width: 180,
            height: 180,
            fit: BoxFit.cover,
          ),
        ),
      );
    }
  }

  // Itens da NavBar
  final List<String> _titles = const ['Início', 'Perfil', 'Configurações'];

  // itens das SubAbas
  final List<String> abas = const [
    'Alterar foto',
    'Alterar nome',
    'Editar E-Mail',
    'Trocar Senha',
    'Reconfigurar Voz',
    'Alterar voz da Ayla',
    'Editar Alarmes',
    'Editar Localização'
  ];

  // Guia Principal
  Widget _buildInicioPage() {
    // Aba Início
    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.start,
      children: [
        Container(
          width: 1300,
          height: 150,
          child: Image.asset('assets/images/logomarcabranco.png'),
        ),
        const SizedBox(height: 50),
        Text(
          'Olá, $nomeUsuario', // Usa a variável de estado aqui
          style: GoogleFonts.josefinSans(fontSize: 30, color: Colors.white),
        ),
        const SizedBox(height: 20),
        Text(
          'Como posso te ajudar hoje?',
          style: GoogleFonts.josefinSans(fontSize: 24, color: Colors.white),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 50),
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
          ),
          child: IconButton(
            icon: const Icon(Icons.mic),
            iconSize: 60,
            color: Colors.white,
            onPressed: () {
              // Ação botão de voz
            },
          ),
        ),
      ],
    );
  }

  // Aba Perfil
  Widget _buildPerfilPage() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.transparent,
          ),
          child: _buildImage(),
        ),
        const SizedBox(height: 25),
        Text(
          'Selecione a opção desejada:',
          style: GoogleFonts.josefinSans(fontSize: 22, color: Colors.white),
        ),
        const SizedBox(height: 30),
        OutlinedButton(
          // Botão para a Sub-Aba Editar foto de Perfil
          onPressed: () {
            Navigator.of(context).push(
                MaterialPageRoute(builder: (context) => _buildAlterarFoto()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar foto de perfil'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Sub-Aba Editar Nome
          onPressed: () {
            Navigator.of(context).push(
                MaterialPageRoute(builder: (context) => _buildAlterarNome()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar Nome'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Sub-Aba Editar E-Mail
          onPressed: () {
            Navigator.of(context).push(
                MaterialPageRoute(builder: (context) => _buildEditarEmail()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar E-Mail'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Sub-Aba Editar Senha
          onPressed: () {
            Navigator.of(context).push(
                MaterialPageRoute(builder: (context) => _buildTrocarSenha()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar Senha'),
        ),
        const SizedBox(height: 50),
        TextButton(
          onPressed: () {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (context) => const LoginScreen()),
            );
          },
          style: TextButton.styleFrom(
            foregroundColor: const Color(0xFF0DAD9E),
            textStyle: const TextStyle(decoration: TextDecoration.underline),
          ),
          child: const Text('Sair da Conta',
              style: TextStyle(color: Color(0xFF0DAD9E), fontSize: 16)),
        ),
      ],
    );
  }

  //Sub-Aba Alterar Foto
  Widget _buildAlterarFoto() {
    return Scaffold(
      appBar: AppBar(
        iconTheme: IconThemeData(color: Colors.white),
        backgroundColor: Color(0xFF0E1315),
        title: Text(
          'Alterar Foto',
          style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
        ),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0),
          child: Container(
            color: Color(0xFF0DAD9E),
            height: 4.0,
          ),
        ),
      ),
      backgroundColor: Color(0xFF0E1315),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            InkWell(
              onTap: () async {
                // Mostra um diálogo para escolher a câmera ou galeria
                var source = await showDialog<ImageSource>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: Text("Escolha a origem da foto"),
                    actions: [
                      TextButton(
                        onPressed: () =>
                            Navigator.pop(context, ImageSource.camera),
                        child: Text("Câmera"),
                      ),
                      TextButton(
                        onPressed: () =>
                            Navigator.pop(context, ImageSource.gallery),
                        child: Text("Galeria"),
                      ),
                    ],
                  ),
                );
                if (source != null) {
                  await _pickImage(source);
                  Navigator.pop(context);
                }
              },
              child: _buildImage(), // Mostra a imagem ou o ícone padrão
            ),
            const SizedBox(height: 60),
            OutlinedButton(
              onPressed: () {
                Navigator.pop(context);
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: Colors.white.withOpacity(0.1),
                side: BorderSide(color: Colors.white, width: 2),
                textStyle: GoogleFonts.josefinSans(fontSize: 20),
                minimumSize: Size(240, 48),
              ),
              child: const Text('Concluído'),
            ),
          ],
        ),
      ),
    );
  }

  //Sub-Aba Alterar Nome
  Widget _buildAlterarNome() {
    final TextEditingController _nomeController = TextEditingController();
    final TextEditingController _sobrenomeController = TextEditingController();
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: AppBar(
            iconTheme: IconThemeData(color: Colors.white),
            title: Text(
              'Alterar Nome',
              style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
            ),
            backgroundColor: Colors.transparent,
            centerTitle: true,
            elevation: 0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
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
              const SizedBox(height: 30),
              TextField(
                textCapitalization: TextCapitalization.sentences,
                controller: _nomeController,
                cursorColor: Colors.white,
                obscureText: false,
                decoration: InputDecoration(
                  labelText: 'Novo Nome',
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
              const SizedBox(height: 20),
              TextField(
                textCapitalization: TextCapitalization.sentences,
                controller: _sobrenomeController,
                cursorColor: Colors.white,
                obscureText: false,
                decoration: InputDecoration(
                  labelText: 'Novo Sobrenome',
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
              const SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  _alterarNomeUsuario(_nomeController.text);
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              )
            ],
          ),
        ),
      ),
    );
  }

  //Sub-Aba Editar E-Mail
  Widget _buildEditarEmail() {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        //Top Bar
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: AppBar(
            iconTheme: IconThemeData(color: Colors.white),
            title: Text(
              'Alterar E-Mail',
              style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
            ),
            backgroundColor: Colors.transparent,
            centerTitle: true,
            elevation: 0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
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
              const SizedBox(height: 30),
              const TextField(
                cursorColor: Colors.white,
                obscureText: false,
                decoration: InputDecoration(
                  labelText: 'Novo E-Mail',
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
              const SizedBox(height: 20),
              const TextField(
                cursorColor: Colors.white,
                obscureText: false,
                decoration: InputDecoration(
                  labelText: 'Confirme o E-Mail',
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
              const SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  //Sub-Aba Editar Senha
  Widget _buildTrocarSenha() {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        //Top Bar
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: AppBar(
            iconTheme: IconThemeData(color: Colors.white),
            title: Text(
              'Alterar Senha',
              style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
            ),
            backgroundColor: Colors.transparent,
            centerTitle: true,
            elevation: 0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
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
              const SizedBox(height: 30),
              const TextField(
                cursorColor: Colors.white,
                obscureText: true, // Para entrada de senha
                decoration: InputDecoration(
                  labelText: 'Nova Senha',
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
              const SizedBox(height: 20),
              const TextField(
                cursorColor: Colors.white,
                obscureText: true, // Para repetir a entrada da senha
                decoration: InputDecoration(
                  labelText: 'Confirme a Senha',
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
              const SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Aba Configurações
  Widget _buildConfiguracoesPage() {
    return Column(
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
          child: const Icon(Icons.settings, size: 80, color: Colors.white),
        ),
        const SizedBox(height: 25),
        Text(
          'Selecione a opção desejada:',
          style: GoogleFonts.josefinSans(fontSize: 22, color: Colors.white),
        ),
        const SizedBox(height: 30),
        OutlinedButton(
          // Botão para a Sub-Aba Reconfigurar Voz
          onPressed: () {
            Navigator.of(context).push(MaterialPageRoute(
                builder: (context) => _buildReconfigurarVoz()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Reconfigurar sua voz'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Sub-Aba Alterar Voz da Ayla
          onPressed: () {
            Navigator.of(context).push(MaterialPageRoute(
                builder: (context) => _buildAlterarVozAyla()));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Alterar voz da Ayla'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Sub-Aba Editar Alarmes
          onPressed: () {
            Navigator.of(context).pushReplacement(MaterialPageRoute(
              builder: (context) => EditarAlarmes(
                  alarmes: alarmes,
                  onAlarmesUpdated: () {
                    setState(() {});
                  }),
            ));
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar Alarmes'),
        ),
        const SizedBox(height: 20),
        OutlinedButton(
          // Botão para a Guia Editar Localização
          onPressed: () {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => PegarLocalizacao()),
            );
          },
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.white.withOpacity(0.1),
            side: const BorderSide(color: Colors.white, width: 2),
            textStyle: GoogleFonts.josefinSans(fontSize: 20),
            minimumSize: const Size(240, 48),
          ),
          child: const Text('Editar Localização'),
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  //Sub-Aba Reconfigurar Voz
  Widget _buildReconfigurarVoz() {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        //Top Bar
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: AppBar(
            iconTheme: IconThemeData(color: Colors.white),
            title: Text(
              'Reconfigurar sua Voz',
              style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
            ),
            backgroundColor: Colors.transparent,
            centerTitle: true,
            elevation: 0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            children: <Widget>[
              Container(
                width: 1300,
                height: 100,
              ),
              OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  //Sub-Aba Reconfigurar Voz da Ayla
  Widget _buildAlterarVozAyla() {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: AppBar(
            iconTheme: IconThemeData(color: Colors.white),
            title: Text(
              'Alterar voz da Ayla',
              style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
            ),
            backgroundColor: Colors.transparent,
            centerTitle: true,
            elevation: 0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            children: <Widget>[
              Container(
                width: 1300,
                height: 100,
              ),
              OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Sistema para mudar de Aba
  Widget _getCurrentPage() {
    switch (currentIndex) {
      case 0:
        return _buildInicioPage();
      case 1:
        return _buildPerfilPage();
      case 2:
        return _buildConfiguracoesPage();
      case 3:
        return _buildAlterarFoto();
      case 4:
        return _buildAlterarNome();
      case 5:
        return _buildEditarEmail();
      case 6:
        return _buildTrocarSenha();
      case 7:
        return _buildReconfigurarVoz();
      case 8:
        return _buildAlterarVozAyla();
      default:
        return _buildInicioPage();
    }
  }

  // NavBar e TopBar
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
          theme: ThemeData(
      primaryColor: Color(0xFF0DAD9E),
      colorScheme: ColorScheme.fromSwatch().copyWith(secondary: Color(0xFF0DAD9E)),
      buttonTheme: ButtonThemeData(
        buttonColor: Color(0xFF0DAD9E),
        textTheme: ButtonTextTheme.primary,
      ),
      dialogBackgroundColor: Color(0xFF0E1315),
      dialogTheme: DialogTheme(
        backgroundColor: Color(0xFF0E1315),
        titleTextStyle: TextStyle(
          color: Colors.black,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
        contentTextStyle: TextStyle(
          color: Colors.black,
          fontSize: 18,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF0DAD9E)),
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF0DAD9E)),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
        ),
        labelStyle: TextStyle(color: Colors.white),
      ),
      iconTheme: IconThemeData(
        color: Colors.black,
      ),
    ),
      home: Scaffold(
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(kToolbarHeight),
          //Top Bar
          child: Container(
            decoration: const BoxDecoration(
              color: Color(0xFF0E1315),
              border: Border(
                bottom: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
              ),
            ),
            child: AppBar(
              title: Text(
                _titles[currentIndex],
                style:
                    GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
              ),
              backgroundColor: Colors.transparent,
              centerTitle: true,
              elevation: 0,
            ),
          ),
        ),
        backgroundColor: const Color(0xFF0E1315),

        body: Center(
          child: _getCurrentPage(),
        ),

        //Navigation Bar
        bottomNavigationBar: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0E1315),
            border: Border(
              top: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
            ),
          ),
          child: BottomNavigationBar(
            iconSize: 40,
            backgroundColor: const Color(0xFF0E1315),
            currentIndex: currentIndex,
            onTap: (int newIndex) {
              setState(() {
                currentIndex = newIndex;
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

//Guia Editar Alarmes
class EditarAlarmes extends StatefulWidget {
  final List<String> alarmes;
  final VoidCallback onAlarmesUpdated;

  const EditarAlarmes(
      {Key? key, required this.alarmes, required this.onAlarmesUpdated})
      : super(key: key);

  @override
  _EditarAlarmesPageState createState() => _EditarAlarmesPageState();
}

class _EditarAlarmesPageState extends State<EditarAlarmes> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () {
            currentIndex = 2;
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => const PerguntaApp()),
            );
          },
        ),
        title: Text(
          'Editar Alarmes',
          style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
        ),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0),
          child: Container(
            color: Color(0xFF0DAD9E),
            height: 4.0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
      floatingActionButton: Container(
        margin: EdgeInsets.only(bottom: 80),
        child: SizedBox(
          width: 70,
          height: 70,
          child: FloatingActionButton(
            onPressed: () {
              Navigator.of(context).push(MaterialPageRoute(
                  builder: (context) => const AdicionarAlarmes()));
            },
            child: Icon(
              Icons.add,
              size: 40,
              color: Color(0xFF0E1315),
            ),
            backgroundColor: Color(0xFF0DAD9E),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10.0),
            ),
          ),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      body: Center(
          child: alarmes.isEmpty
              ? Text(
                  "Nenhum alarme configurado.",
                  style: GoogleFonts.josefinSans(
                      fontSize: 20, color: Colors.white),
                )
              : ListView.builder(
                  itemCount: alarmes.length,
                  itemBuilder: (context, index) {
                    return Column(
                      children: [
                        ListTile(
                          leading: Icon(Icons.alarm, color: Colors.white),
                          title: Text(
                            alarmes[index].split(" - ")[0],
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.white, fontSize: 24),
                          ),
                          trailing: Text(
                            alarmes[index].split(" - ")[1],
                            style: TextStyle(color: Colors.white, fontSize: 24),
                          ),
                        ),
                        Divider(
                            color: Color(0xFF0DAD9E),
                            thickness: 1,
                            height: 1), // Sem padding
                      ],
                    );
                  },
                )),
    );
  }
}

// Guia Adicionar Alarmes
class AdicionarAlarmes extends StatefulWidget {
  const AdicionarAlarmes({Key? key}) : super(key: key);

  @override
  _AdicionarAlarmesState createState() => _AdicionarAlarmesState();
}

class _AdicionarAlarmesState extends State<AdicionarAlarmes> {
  final TextEditingController alarmNameController = TextEditingController();
  TimeOfDay selectedTime = TimeOfDay(hour: 0, minute: 0);

  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: selectedTime,
    );
    if (picked != null && picked != selectedTime) {
      setState(() {
        selectedTime = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () {
            currentIndex = 2;
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => const PerguntaApp()),
            );
          },
        ),
        title: Text(
          'Adicionar Alarmes',
          style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
        ),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0),
          child: Container(
            color: Color(0xFF0DAD9E),
            height: 4.0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              TextField(
                controller: alarmNameController,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  labelText: 'Nome do alarme',
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
              SizedBox(height: 20),
              OutlinedButton(
                onPressed: () => _selectTime(context),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Selecionar Horário'),
              ),
              SizedBox(height: 20),
              Text(
                'Horário selecionado: ${selectedTime.format(context)}',
                style: TextStyle(color: Colors.white, fontSize: 20),
              ),
              SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  String alarmName = alarmNameController.text.isEmpty
                      ? ''
                      : alarmNameController.text;
                  setState(() {
                    alarmes.add("$alarmName - ${selectedTime.format(context)}");
                  });
                  Navigator.of(context).push(MaterialPageRoute(
                    builder: (context) => EditarAlarmes(
                      alarmes: alarmes,
                      onAlarmesUpdated: () => setState(() {}),
                    ),
                  ));
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Concluído'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Guia Localização
class PegarLocalizacao extends StatefulWidget {
  const PegarLocalizacao({super.key});

  @override
  State createState() => _PegarLocalizacaoState();
}

class _PegarLocalizacaoState extends State<PegarLocalizacao> {
  late GoogleMapController mapController;
  Set<Marker> markers = {};

  final LatLng _center = const LatLng(-15.793889, -47.882778);

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    _updateMarker(_center);
  }

  void _updateMarker(LatLng newLocation) {
    setState(() {
      markers.clear();
      markers.add(
        Marker(
          markerId: const MarkerId('selectedLocation'),
          position: newLocation,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () {
            currentIndex = 2;
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => const PerguntaApp()),
            );
          },
        ),
        title: Text(
          'Editar Localização',
          style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
        ),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0),
          child: Container(
            color: Color(0xFF0DAD9E),
            height: 4.0,
          ),
        ),
      ),
      body: GoogleMap(
        onMapCreated: _onMapCreated,
        onTap: _updateMarker, // Atualiza o marcador quando o mapa é clicado
        initialCameraPosition: CameraPosition(target: _center, zoom: 11.0),
        markers: markers,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Color(0xFF0E1315),
          border: Border(
            top: BorderSide(color: Color(0xFF0DAD9E), width: 4.0),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: OutlinedButton(
            onPressed: () {
              currentIndex = 2;
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => const PerguntaApp()),
              );
            },
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              backgroundColor: Colors.white.withOpacity(0.1),
              side: BorderSide(color: Colors.white, width: 2),
              textStyle: GoogleFonts.josefinSans(fontSize: 20),
              minimumSize: Size(240, 48),
            ),
            child: const Text('Concluído'),
          ),
        ),
      ),
    );
  }
}

// Guia Cadastro Concluído
class RegistrationCompletePage extends StatelessWidget {
  const RegistrationCompletePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0E1315),
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
            const SizedBox(height: 40),
            Text(
              "Obrigado por se cadastrar!",
              style: GoogleFonts.josefinSans(fontSize: 24, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 60),
            OutlinedButton(
              onPressed: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: Colors.white.withOpacity(0.1),
                side: BorderSide(color: Colors.white, width: 2),
                textStyle: GoogleFonts.josefinSans(fontSize: 20),
                minimumSize: Size(240, 48),
              ),
              child: const Text('Concluído'),
            ),
          ],
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
    );
  }
}

// Guia de Cadastro
class RegisterPage extends StatelessWidget {
  const RegisterPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0E1315),
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
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const RegistrationCompletePage()),
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Avançar'),
              ),
            ],
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
    );
  }
}

// Guia Alterar Senha Concluido
class ThankYouPage extends StatelessWidget {
  const ThankYouPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0E1315),
        iconTheme: const IconThemeData(color: Colors.white),
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
            const SizedBox(height: 40),
            Text(
              "Enviamos um link para\n seu E-mail.",
              style: GoogleFonts.josefinSans(fontSize: 24, color: Colors.white),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 60),
            OutlinedButton(
              onPressed: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: Colors.white.withOpacity(0.1),
                side: BorderSide(color: Colors.white, width: 2),
                textStyle: GoogleFonts.josefinSans(fontSize: 20),
                minimumSize: Size(240, 48),
              ),
              child: const Text('Concluído'),
            ),
          ],
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
    );
  }
}

// Guia Esqueci a Senha
class ForgotPasswordPage extends StatelessWidget {
  const ForgotPasswordPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text("Recuperar Senha",
            style: GoogleFonts.josefinSans(color: Colors.white)),
        backgroundColor: const Color(0xFF0E1315),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
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
              const SizedBox(height: 20),
              Text(
                "Digite seu e-mail para receber as instruções de recuperação de senha.",
                style:
                    GoogleFonts.josefinSans(fontSize: 18, color: Colors.white),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              const TextField(
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
              const SizedBox(height: 40),
              OutlinedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const ThankYouPage()),
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Avançar'),
              ),
            ],
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
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

// Guia de Login
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
    Color themeColor =
        const Color(0xFF0DAD9E); // Definição da cor personalizada

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
              const SizedBox(height: 20),
              TextField(
                controller: emailController,
                cursorColor: Colors.white, // Cor do cursor
                style: const TextStyle(
                    color: Colors.white), // Cor do texto digitado
                decoration: InputDecoration(
                  labelText: "E-mail",
                  labelStyle: TextStyle(color: themeColor),
                  border: const OutlineInputBorder(),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: themeColor, width: 2.0),
                  ),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: passwordController,
                cursorColor: Colors.white, // Cor do cursor
                style: const TextStyle(
                    color: Colors.white), // Cor do texto digitado
                decoration: InputDecoration(
                  labelText: "Senha",
                  labelStyle: TextStyle(color: themeColor),
                  border: const OutlineInputBorder(),
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
              const SizedBox(height: 20),
              OutlinedButton(
                onPressed: () {
                  currentIndex = 0;
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const PerguntaApp()),
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Login'),
              ),
              const SizedBox(height: 20),
              Row(
                children: <Widget>[
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(left: 10.0, right: 20.0),
                      child: const Divider(
                        color: Color(0xFF0DAD9E),
                        height: 36,
                      ),
                    ),
                  ),
                  const Text("Novo aqui?",
                      style: TextStyle(
                        color: Color(0xFF0DAD9E),
                        fontWeight: FontWeight.w600,
                      )),
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(left: 20.0, right: 10.0),
                      child: const Divider(
                        color: Color(0xFF0DAD9E),
                        height: 36,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              OutlinedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const RegisterPage()),
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Cadastre-se'),
              ),
            ],
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315), // Cor de fundo do Scaffold
    );
  }
}
