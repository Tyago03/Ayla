import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/services.dart';
import 'dart:io';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';

//Cores principais usadas:
// Plano de fundo: #0E1315
// Cor dos realces: #0DAD9E

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (Firebase.apps.isEmpty) {
    // Verifica se não há instâncias já inicializadas.
    await Firebase.initializeApp(
        name: "dev project", options: DefaultFirebaseOptions.currentPlatform);
  }
  runApp(const MyApp());
}

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
  late stt.SpeechToText _speech;
  bool _isListening = false;
  String _text = "Pressione o ícone do microfone para falar";
  late FlutterTts flutterTts;

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _loadUserName();
    flutterTts = FlutterTts();
  }

  void _logout() async {
    await FirebaseAuth.instance.signOut(); // Desloga o usuário
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
          builder: (context) =>
              const LoginScreen()), // Redireciona para a tela de login
    );
  }

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

  Future<void> _salvarAlarme(String nome, TimeOfDay horario) async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      // Cria um documento com um ID gerado automaticamente na coleção 'alarmes'
      await FirebaseFirestore.instance.collection('alarmes').add({
        'uid': user.uid, // Associa o alarme ao usuário
        'nome': nome,
        'horario': "${horario.hour}:${horario.minute}",
      });
    }
  }

  String nomeUsuario = 'User';

  Future<void> _loadUserName() async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      DocumentSnapshot userData = await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .get();
      setState(() {
        nomeUsuario = userData['nome'] ?? 'User';
      });
    }
  }

  XFile? _imageFile;

  void _alterarNomeUsuario(String novoNome) async {
    if (novoNome.isNotEmpty && FirebaseAuth.instance.currentUser != null) {
      String uid = FirebaseAuth.instance.currentUser!.uid;
      await FirebaseFirestore.instance.collection('users').doc(uid).update({
        'nome': novoNome,
      });
      setState(() {
        nomeUsuario = novoNome;
      });
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await ImagePicker().pickImage(source: source);
      if (pickedFile != null) {
        setState(() {
          _imageFile = pickedFile;
        });
        Navigator.pop(context); // Volta para a tela anterior (Perfil)
      }
    } catch (e) {
      print('Erro ao pegar a imagem: $e');
    }
  }

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
            color: Color(0xFF0DAD9E),
            width: 4,
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

  final List<String> _titles = const ['Início', 'Perfil', 'Configurações'];

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

  Widget _buildInicioPage() {
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
          'Olá, $nomeUsuario',
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
            onPressed: _listen,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          _text,
          style: TextStyle(color: Colors.white),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) {
          print('onStatus: $val');
          if (val == 'notListening') {
            setState(() => _isListening = false);
          }
        },
        onError: (val) {
          print('onError: $val');
          setState(() => _isListening = false);
        },
      );
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (val) => setState(() {
            _text = val.recognizedWords;
            if (val.hasConfidenceRating && val.confidence > 0) {
              _sendCommand(_text);
            }
          }),
        );
      }
    } else {
      setState(() => _isListening = false);
      _speech.stop();
    }
  }

  Future<void> _sendCommand(String command) async {
    final response = await http.post(
      Uri.parse(
          'https://7475-2804-14c-6591-48b4-7d8f-a1f5-b48-38ee.ngrok-free.app/command/'), // substitua pelo IP do seu computador
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'text': command,
      }),
    );

    if (response.statusCode == 200) {
      final result = jsonDecode(utf8.decode(response.bodyBytes));
      setState(() {
        _text = result['message']; // Atualiza o texto com a resposta do FastAPI
      });
      await flutterTts.speak(_text); // Converte a resposta em voz
    } else {
      setState(() {
        _text = 'Erro ao processar o comando';
      });
      await flutterTts.speak(_text); // Converte a mensagem de erro em voz
    }
  }

  Widget _buildPerfilPage() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 140, // Um pouco maior para acomodar o círculo branco
          height: 140, // Um pouco maior para acomodar o círculo branco
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.white, // Apenas o círculo branco
              width: 0, // Tamanho da borda branca
            ),
          ),
          child: Container(
            width: 120, // Tamanho original do ícone de perfil
            height: 120, // Tamanho original do ícone de perfil
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.transparent,
            ),
            child: _buildImage(), // Ícone ou foto de perfil escolhida
          ),
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
          onPressed: _logout, // Chama o método de logout
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

// Sub-Aba Alterar Foto
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
              onTap: () {
                _showPhotoOptionsDialog(context); // Exibe o pop-up de opções
              },
              child: Stack(
                children: [
                  // Ícone de perfil com círculo ao redor
                  Container(
                    width: 140,
                    height: 140,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white, // Círculo branco ao redor
                        width: 4,
                      ),
                    ),
                    child: _buildImage(), // Mostra a imagem ou o ícone padrão
                  ),
                  // Ícone de "+" no canto inferior direito
                  Positioned(
                    right: 0,
                    bottom: 0,
                    child: Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color(0xFF0DAD9E), // Cor de fundo do botão "+"
                      ),
                      padding:
                          EdgeInsets.all(8), // Ajusta o espaço ao redor do "+"
                      child: Icon(
                        Icons.add, // Ícone de "+"
                        color: Colors.white,
                        size: 24,
                      ),
                    ),
                  ),
                ],
              ),
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

// Função para mostrar opções de foto, incluindo remover foto se já houver uma
  Future<void> _showPhotoOptionsDialog(BuildContext context) async {
    var source = await showDialog<ImageSource>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Escolha a origem da foto"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, ImageSource.camera),
            child: Text("Câmera"),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, ImageSource.gallery),
            child: Text("Galeria"),
          ),
          if (_imageFile !=
              null) // Apenas exibe essa opção se houver uma foto selecionada
            TextButton(
              onPressed: () {
                setState(() {
                  _imageFile = null; // Remove a foto
                });
                Navigator.pop(context); // Fecha o diálogo
                Navigator.pop(context); // Volta para a tela de perfil
              },
              child: Text("Remover foto"),
            ),
        ],
      ),
    );
    if (source != null) {
      await _pickImage(source); // Escolha de imagem, já faz o pop ao concluir
    }
  }

  //Sub-Aba Alterar Nome
  Widget _buildAlterarNome() {
    final TextEditingController _nomeController = TextEditingController();
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
                  labelText: 'Insira seu primeiro nome',
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

  Widget _buildEditarEmail() {
    final TextEditingController _emailController = TextEditingController();
    final TextEditingController _senhaController =
        TextEditingController(); // Para reautenticar

    return Scaffold(
      appBar: AppBar(
        iconTheme: IconThemeData(color: Colors.white),
        title: Text('Alterar E-Mail',
            style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28)),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
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
                controller: _emailController,
                cursorColor: Colors.white,
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
              TextField(
                controller: _senhaController,
                cursorColor: Colors.white,
                obscureText: true, // Campo de senha para reautenticação
                decoration: InputDecoration(
                  labelText: 'Senha atual',
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
              OutlinedButton(
                onPressed: () async {
                  await _updateEmail(
                      _emailController.text, _senhaController.text);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Alterar E-mail'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _updateEmail(String newEmail, String senha) async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null && newEmail.isNotEmpty) {
      try {
        // Reautenticar o usuário
        AuthCredential credential = EmailAuthProvider.credential(
          email: user.email!,
          password: senha,
        );
        await user.reauthenticateWithCredential(credential);

        // Atualizar o e-mail
        await user.updateEmail(newEmail);

        // Notificar o usuário por e-mail (simulação)
        // Aqui você pode usar o Firebase Functions ou outro serviço para enviar o e-mail
        // Em um ambiente real, você configuraria isso no backend
        await sendEmailNotification(newEmail);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("E-mail atualizado com sucesso")),
        );

        // Navegar de volta para a tela anterior após o sucesso
        Navigator.pop(
            context); // Envia o usuário de volta para a página anterior
      } on FirebaseAuthException catch (e) {
        String errorMessage = "Erro ao alterar o e-mail.";
        if (e.code == 'requires-recent-login') {
          errorMessage = "Por favor, faça login novamente para continuar.";
        } else if (e.code == 'email-already-in-use') {
          errorMessage = "O e-mail já está em uso.";
        } else if (e.code == 'invalid-email') {
          errorMessage = "E-mail inválido.";
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(errorMessage), backgroundColor: Colors.red),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Erro desconhecido: $e."),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> sendEmailNotification(String email) async {
    // Aqui você integraria o serviço de envio de e-mail
    // Pode usar Firebase Functions ou algum serviço de terceiros como SendGrid, Mailgun etc.
    print("E-mail de confirmação enviado para $email");
  }

  // Sub-Aba Editar Senha
  Widget _buildTrocarSenha() {
    return Scaffold(
      appBar: AppBar(
        iconTheme: IconThemeData(color: Colors.white),
        title: Text('Alterar Senha',
            style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28)),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
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
              OutlinedButton(
                onPressed: () async {
                  await _sendPasswordResetEmail();
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Enviar Link de Redefinição'),
              ),
            ],
          ),
        ),
      ),
    );
  }

// Função para enviar o e-mail de redefinição de senha
  Future<void> _sendPasswordResetEmail() async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      try {
        await FirebaseAuth.instance.sendPasswordResetEmail(email: user.email!);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(
                  "Link de redefinição de senha enviado para ${user.email}. Verifique seu e-mail.")),
        );
      } catch (e) {
        print('Erro ao enviar o e-mail de redefinição: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content:
                Text("Erro ao enviar o link de redefinição. Tente novamente."),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
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
                onAlarmesUpdated: () {
                  setState(() {});
                },
              ),
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
        colorScheme:
            ColorScheme.fromSwatch().copyWith(secondary: Color(0xFF0DAD9E)),
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
  final VoidCallback onAlarmesUpdated;

  const EditarAlarmes({Key? key, required this.onAlarmesUpdated})
      : super(key: key);

  @override
  _EditarAlarmesPageState createState() => _EditarAlarmesPageState();
}

class _EditarAlarmesPageState extends State<EditarAlarmes> {
  List<String> alarmes = []; // Lista de alarmes

  // Função para carregar alarmes do Firebase
  Future<void> _carregarAlarmes() async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      QuerySnapshot snapshot = await FirebaseFirestore.instance
          .collection('alarmes')
          .where('uid', isEqualTo: user.uid)
          .get();

      setState(() {
        alarmes = snapshot.docs.map((doc) {
          Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
          return "${data['nome']} - ${data['horario']}";
        }).toList();
      });
    }
  }

  @override
  void initState() {
    super.initState();
    _carregarAlarmes(); // Carrega os alarmes do Firebase ao iniciar
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
      body: Center(
        child: alarmes.isEmpty
            ? Text(
                "Nenhum alarme configurado.",
                style:
                    GoogleFonts.josefinSans(fontSize: 20, color: Colors.white),
              )
            : ListView.builder(
                itemCount: alarmes.length,
                itemBuilder: (context, index) {
                  var partes = alarmes[index].split(" - ");
                  String horario = partes.length > 1
                      ? partes[1]
                      : "Horário não definido"; // Verificação corrigida

                  return Column(
                    children: [
                      ListTile(
                        title: Center(
                          // Mantém o nome do alarme centralizado
                          child: Text(
                            partes[0], // Nome do alarme
                            style: TextStyle(color: Colors.white, fontSize: 24),
                          ),
                        ),
                        leading: Text(
                          // Coloca o horário na esquerda
                          horario,
                          style: TextStyle(color: Colors.white, fontSize: 24),
                        ),
                        trailing: PopupMenuButton<String>(
                          onSelected: (String result) {
                            if (result == 'Editar') {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (context) => EditarAlarmePage(
                                    alarme: alarmes[index],
                                    onSave: (String novoNome,
                                        TimeOfDay? novoHorario) async {
                                      // Mantém o horário anterior caso novoHorario seja nulo
                                      String horarioAntigo = partes[1];
                                      TimeOfDay horarioFinal = novoHorario ??
                                          TimeOfDay(
                                            hour: int.parse(
                                                horarioAntigo.split(":")[0]),
                                            minute: int.parse(
                                                horarioAntigo.split(":")[1]),
                                          );

                                      await _editarAlarme(
                                          alarmes[index],
                                          novoNome,
                                          horarioFinal); // Edita no Firebase
                                      setState(() {
                                        alarmes[index] =
                                            "$novoNome";
                                      });
                                    },
                                  ),
                                ),
                              );
                            } else if (result == 'Excluir') {
                              _excluirAlarme(
                                  alarmes[index]); // Exclui do Firebase
                              setState(() {
                                alarmes.removeAt(index);
                              });
                            }
                          },
                          itemBuilder: (BuildContext context) =>
                              <PopupMenuEntry<String>>[
                            const PopupMenuItem<String>(
                              value: 'Editar',
                              child: Text('Editar Alarme'),
                            ),
                            const PopupMenuItem<String>(
                              value: 'Excluir',
                              child: Text('Excluir Alarme'),
                            ),
                          ],
                        ),
                      ),
                      Divider(
                        color: Color(0xFF0DAD9E),
                        thickness: 1,
                        height: 1,
                      ),
                    ],
                  );
                },
              ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => AdicionarAlarmes(),
            ),
          );
        },
        child: Icon(Icons.add),
        backgroundColor: Color(0xFF0DAD9E), // A cor do botão flutuante
      ),
    );
  }

  // Função para excluir alarme
  Future<void> _excluirAlarme(String alarme) async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      QuerySnapshot snapshot = await FirebaseFirestore.instance
          .collection('alarmes')
          .where('uid', isEqualTo: user.uid)
          .where('nome', isEqualTo: alarme.split(' - ')[0])
          .get();

      if (snapshot.docs.isNotEmpty) {
        DocumentSnapshot doc = snapshot.docs.first;
        await doc.reference.delete();
      }
    }
  }

  // Função para editar alarme
  Future<void> _editarAlarme(
      String alarmeAntigo, String novoNome, TimeOfDay novoHorario) async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      QuerySnapshot snapshot = await FirebaseFirestore.instance
          .collection('alarmes')
          .where('uid', isEqualTo: user.uid)
          .where('nome', isEqualTo: alarmeAntigo.split(' - ')[0])
          .get();

      if (snapshot.docs.isNotEmpty) {
        DocumentSnapshot doc = snapshot.docs.first;
        await doc.reference.update({
          'nome': novoNome,
          'horario': "${novoHorario.hour}:${novoHorario.minute}",
        });

        setState(() {
          print(
              "Alarme atualizado: $novoNome - ${novoHorario.hour}:${novoHorario.minute}");
        });
      }
    }
  }
}


class EditarAlarmePage extends StatefulWidget {
  final String alarme;
  final Function(String, TimeOfDay) onSave;

  const EditarAlarmePage({Key? key, required this.alarme, required this.onSave})
      : super(key: key);

  @override
  _EditarAlarmePageState createState() => _EditarAlarmePageState();
}

class _EditarAlarmePageState extends State<EditarAlarmePage> {
  late TextEditingController alarmNameController;
  TimeOfDay? selectedTime;
  String? horarioAntigo;

  @override
  void initState() {
    super.initState();
    // Inicializa o controlador com o nome do alarme
    alarmNameController = TextEditingController(
      text: widget.alarme.split(" - ")[0],
    );

    // Tenta inicializar o horário do alarme
    try {
      List<String> partes = widget.alarme.split(" - ");
      if (partes.length > 1) {
        horarioAntigo = partes[1]; // Pega o horário antigo
      } else {
        horarioAntigo = null;
      }
    } catch (e) {
      horarioAntigo = null;
    }

    // Se o horário antigo existe, tenta converter para TimeOfDay
    if (horarioAntigo != null) {
      try {
        final timeParts = horarioAntigo!.split(":");
        selectedTime = TimeOfDay(
          hour: int.parse(timeParts[0]),
          minute: int.parse(timeParts[1]),
        );
      } catch (e) {
        selectedTime = null;
      }
    } else {
      selectedTime = null; // Se não houver horário antigo, inicia como null
    }
  }

  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: selectedTime ?? TimeOfDay.now(),
    );
    if (picked != null) {
      setState(() {
        selectedTime = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Editar Alarme',
            style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28)),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.white),
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(4.0),
          child: Container(
            color: Color(0xFF0DAD9E),
            height: 4.0,
          ),
        ),
      ),
      backgroundColor: const Color(0xFF0E1315),
      body: Padding(
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
                  borderSide: BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
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
              selectedTime != null
                  ? 'Horário selecionado: ${selectedTime!.format(context)}'
                  : horarioAntigo != null
                      ? 'Horário atual: $horarioAntigo'
                      : 'Horário não selecionado',
              style: TextStyle(color: Colors.white, fontSize: 20),
            ),
            SizedBox(height: 40),
            OutlinedButton(
              onPressed: () {
                String novoNome = alarmNameController.text;
                TimeOfDay? novoHorario = selectedTime;

                // Se o novo horário for null, mantém o horário antigo
                if (novoHorario == null && horarioAntigo != null) {
                  final timeParts = horarioAntigo!.split(":");
                  novoHorario = TimeOfDay(
                    hour: int.parse(timeParts[0]),
                    minute: int.parse(timeParts[1]),
                  );
                }

                widget.onSave(
                  novoNome,
                  novoHorario ?? TimeOfDay.now(), // Garante um horário
                );

                Navigator.of(context).pop(); // Fecha a tela após salvar
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: Colors.white.withOpacity(0.1),
                side: BorderSide(color: Colors.white, width: 2),
                textStyle: GoogleFonts.josefinSans(fontSize: 20),
                minimumSize: Size(240, 48),
              ),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
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

  Future<void> _salvarAlarme(String nome, TimeOfDay horario) async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      // Cria um documento com um ID gerado automaticamente na coleção 'alarmes'
      await FirebaseFirestore.instance.collection('alarmes').add({
        'uid': user.uid, // Associa o alarme ao usuário
        'nome': nome,
        'horario': "${horario.hour}:${horario.minute}",
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
                onPressed: () async {
                  String alarmName = alarmNameController.text.isEmpty
                      ? ''
                      : alarmNameController.text;
                  await _salvarAlarme(
                      alarmName, selectedTime); // Salva no Firebase
                  Navigator.of(context).push(MaterialPageRoute(
                    builder: (context) => EditarAlarmes(
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

// Guia Localização com Barra de Pesquisa com fundo personalizado e sem áreas brancas
class PegarLocalizacao extends StatefulWidget {
  const PegarLocalizacao({super.key});

  @override
  State createState() => _PegarLocalizacaoState();
}

class _PegarLocalizacaoState extends State<PegarLocalizacao> {
  late GoogleMapController mapController;
  Set<Marker> markers = {};
  final TextEditingController _searchController = TextEditingController();

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    _loadUserLocation(); // Chama a função para carregar a localização
  }

  // Carrega a localização do usuário com base no CEP salvo no Firestore
  void _loadUserLocation() async {
    User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      DocumentSnapshot userDoc = await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .get();
      if (userDoc.exists) {
        var data = userDoc.data() as Map<String, dynamic>;
        if (data.containsKey('cep')) {
          String cep = data['cep'];
          _getCoordinatesFromCEP(cep); // Converte CEP em coordenadas
        }
      }
    }
  }

  // Obtém as coordenadas a partir do CEP ou endereço
  Future<void> _getCoordinatesFromCEP(String address) async {
    var response = await http.get(Uri.parse(
        'https://maps.googleapis.com/maps/api/geocode/json?address=$address&key=AIzaSyBnEMFheAW0dZNckqKMEl0WRVP7RuewGw4'));
    var data = jsonDecode(response.body);
    if (data['results'].isNotEmpty) {
      var coordinates = data['results'][0]['geometry']['location'];
      LatLng newLocation = LatLng(coordinates['lat'], coordinates['lng']);
      _updateMarker(newLocation);
      mapController.moveCamera(CameraUpdate.newLatLng(newLocation));
    }
  }

  // Atualiza o marcador no mapa
  void _updateMarker(LatLng newLocation) {
    setState(() {
      markers.clear();
      markers.add(Marker(
        markerId: const MarkerId('selectedLocation'),
        position: newLocation,
      ));
    });
  }

  // Ação de pesquisa ao pressionar o botão de pesquisa
  void _onSearch() {
    String searchQuery = _searchController.text;
    if (searchQuery.isNotEmpty) {
      _getCoordinatesFromCEP(searchQuery);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () {
            Navigator.pushReplacement(context,
                MaterialPageRoute(builder: (context) {
              currentIndex = 2;
              return PerguntaApp();
            }));
          },
        ),
        title: Text(
          'Editar Localização',
          style: GoogleFonts.josefinSans(color: Colors.white, fontSize: 28),
        ),
        backgroundColor: Color(0xFF0E1315),
        centerTitle: true,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Barra de pesquisa sem áreas brancas
          Container(
            color:
                Color(0xFF0E1315), // Cor de fundo externa da barra de pesquisa
            padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    cursorColor: Colors.white,
                    decoration: InputDecoration(
                      filled: true,
                      fillColor:
                          Color(0xFF0E1315), // Cor interna da barra de pesquisa
                      hintText: 'Pesquisar por CEP ou endereço...',
                      hintStyle: TextStyle(color: Colors.white70),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Color(0xFF0DAD9E)),
                        borderRadius: BorderRadius.circular(10.0),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderSide:
                            BorderSide(color: Color(0xFF0DAD9E), width: 2.0),
                        borderRadius: BorderRadius.circular(10.0),
                      ),
                      labelStyle: TextStyle(color: Color(0xFF0DAD9E)),
                    ),
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.search, color: Color(0xFF0DAD9E)),
                  onPressed: _onSearch,
                ),
              ],
            ),
          ),
          Expanded(
            child: GoogleMap(
              onMapCreated: _onMapCreated,
              initialCameraPosition: CameraPosition(
                target:
                    LatLng(-15.793889, -47.882778), // Coordenada inicial padrão
                zoom: 15.0,
              ),
              markers: markers,
            ),
          ),
        ],
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
        iconTheme: const IconThemeData(color: Colors.white),
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
  final TextEditingController emailController = TextEditingController();
  final TextEditingController senhaController = TextEditingController();
  final TextEditingController repetirSenhaController = TextEditingController();
  final TextEditingController nomeController = TextEditingController();
  final TextEditingController cepController = TextEditingController();

  RegisterPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final TextEditingController cepController = TextEditingController();

    return Scaffold(
      appBar: AppBar(
        iconTheme: const IconThemeData(color: Colors.white),
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
              TextField(
                controller: nomeController,
                cursorColor: Colors.white,
                decoration: InputDecoration(
                  labelText: 'Primeiro Nome',
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
                textCapitalization: TextCapitalization.words,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: emailController,
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
              TextField(
                controller: cepController,
                cursorColor: Colors.white,
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(
                      8), // Garante que só temos espaço para 8 dígitos e 1 hífen
                ],
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
                onChanged: (value) {
                  // Verifica se precisa adicionar o hífen depois do quinto dígito
                  String newText;
                  if (value.length >= 6 && !value.contains('-')) {
                    newText = value.substring(0, 5) + '-' + value.substring(5);
                  } else {
                    newText = value;
                  }
                  if (newText != value) {
                    cepController.value = TextEditingValue(
                      text: newText,
                      selection:
                          TextSelection.collapsed(offset: newText.length),
                    );
                  }
                },
              ),
              const SizedBox(height: 20),
              TextField(
                controller: senhaController,
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
              TextField(
                controller: repetirSenhaController,
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
                onPressed: () async {
                  if (senhaController.text != repetirSenhaController.text) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text("As senhas não coincidem."),
                        backgroundColor: Colors.red,
                      ),
                    );
                    return;
                  }

                  try {
                    UserCredential userCredential = await FirebaseAuth.instance
                        .createUserWithEmailAndPassword(
                      email: emailController.text,
                      password: senhaController.text,
                    );
                    User? user = userCredential.user;
                    await FirebaseFirestore.instance
                        .collection('users')
                        .doc(user!.uid)
                        .set({
                      'nome': nomeController.text,
                      'cep': cepController.text,
                    });
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context) =>
                              const RegistrationCompletePage()),
                    );
                  } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text("Erro ao registrar: ${e.toString()}"),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.white.withOpacity(0.1),
                  side: BorderSide(color: Colors.white, width: 2),
                  textStyle: GoogleFonts.josefinSans(fontSize: 20),
                  minimumSize: Size(240, 48),
                ),
                child: const Text('Avançar'),
              )
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
      resizeToAvoidBottomInset:
          false, // Adicionado para desativar a adaptação automática ao teclado
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const SizedBox(height: 80),
              Container(
                width: 1300,
                height: 80,
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
                onPressed: () async {
                  if (emailController.text.isEmpty ||
                      passwordController.text.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Por favor, insira seu e-mail e senha.'),
                        backgroundColor: Colors.red,
                      ),
                    );
                    return; // Impede a execução adicional se os campos estiverem vazios
                  }

                  try {
                    // Tentativa de login com o FirebaseAuth
                    UserCredential userCredential =
                        await FirebaseAuth.instance.signInWithEmailAndPassword(
                      email: emailController.text,
                      password: passwordController.text,
                    );

                    // Navegação para a página principal só ocorre após o sucesso do login
                    currentIndex = 0;
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                          builder: (context) => const PerguntaApp()),
                    );
                  } on FirebaseAuthException catch (e) {
                    String errorMessage = 'Email ou Senha inválidos.';
                    if (e.code == 'user-not-found') {
                      errorMessage =
                          'Nenhum usuário encontrado para esse e-mail.';
                    } else if (e.code == 'wrong-password') {
                      errorMessage = 'Senha incorreta.';
                    }
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(errorMessage),
                        backgroundColor: Colors.red,
                      ),
                    );
                  } catch (e) {
                    // Tratar quaisquer outros erros que possam ocorrer
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Erro de login: ${e.toString()}'),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
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
                    MaterialPageRoute(builder: (context) => RegisterPage()),
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
      backgroundColor: const Color(0xFF0E1315),
    );
  }
}
