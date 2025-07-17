import 'package:flutter/material.dart'; #main.dart
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Real-time Thai Subtitles',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: RealTimeSubtitlePage(),
    );
  }
}

class RealTimeSubtitlePage extends StatefulWidget {
  @override
  _RealTimeSubtitlePageState createState() => _RealTimeSubtitlePageState();
}

class _RealTimeSubtitlePageState extends State<RealTimeSubtitlePage> {
  late stt.SpeechToText _speech;
  String _previousSubtitle = "";
  String _currentSubtitle = "";
  String _transformedSubtitle = "";
  bool _isListening = false;

  final String serverUrl = "http://10.16.36.12:5000/process";  // ✅ ใช้ IP จริงแทน localhost

  // 🔹 สีของคำที่ต้องเปลี่ยน
  final Map<String, Color> colorDict = {
    "สีแดง": Colors.red,
    "สีส้ม": const Color.fromARGB(163, 255, 153, 0),
    "สีเหลือง": Colors.yellow,
    "สีเขียว": Colors.green,
    "สีน้ำเงิน": const Color.fromARGB(255, 24, 103, 167),
    "สีฟ้า": Colors.lightBlue,
    "สีม่วง": Colors.purple,
    "สีชมพู": const Color.fromARGB(255, 240, 6, 189),
    "สีดำ": Colors.black,
    "สีขาว": Colors.white,
    "สีเทา": Colors.grey,
    "สีน้ำตาล": Colors.brown,
    "วันจันทร์": Colors.yellow,
    "วันอังคาร": const Color.fromARGB(255, 240, 6, 189),
    "วันพุธ": Colors.green,
    "วันพฤหัสบดี": const Color.fromARGB(163, 255, 153, 0),
    "วันศุกร์": const Color.fromARGB(255, 24, 103, 167),
    "วันเสาร์": Colors.purple,
    "วันอาทิตย์": Colors.red,
  };

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _startListening();
  }

  Future<void> _processSubtitle() async {
    print("📤 ส่งข้อมูลไป API: $_previousSubtitle");

    final response = await http.post(
      Uri.parse(serverUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"text": _previousSubtitle}),
    );

    print("📥 สถานะ API: ${response.statusCode}");
    print("📥 ข้อมูลที่ได้รับ: ${response.body}");

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      setState(() {
        _transformedSubtitle = data["result"];
      });
    } else {
      setState(() {
        _transformedSubtitle = "❌ ไม่สามารถแปลงประโยคได้";
      });
    }
  }

  void _startListening() async {
    bool available = await _speech.initialize(
      onError: (error) => print("Speech Error: $error"),
      onStatus: (status) {
        if (status == 'notListening' && _isListening) {
          _shiftSubtitles();
          _startListening();
        }
      },
    );

    if (available) {
      setState(() => _isListening = true);
      _speech.listen(
        onResult: (result) {
          setState(() {
            _currentSubtitle = result.recognizedWords;
          });
        },
        localeId: "th-TH",
        listenFor: Duration(seconds: 10),
        pauseFor: Duration(seconds: 2),
      );
    }
  }

  void _shiftSubtitles() {
    if (_currentSubtitle.isNotEmpty) {
      setState(() {
        _previousSubtitle = _currentSubtitle;
        _currentSubtitle = "";
      });

      _processSubtitle();
    }
  }

  // 🔹 ฟังก์ชันแปลง `String` เป็น `RichText` ที่มีสี
  Widget _buildColoredText(String text) {
    List<String> words = text.split(" ");
    return RichText(
      text: TextSpan(
        children: words.map((word) {
          return TextSpan(
            text: "$word ",
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: colorDict.containsKey(word) ? colorDict[word] : Colors.black,
            ),
          );
        }).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Real-time Thai Subtitles')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // 🔹 ข้อความที่ถูกแปลง + แสดงสี
            Text(
              "📌 ประโยคที่ถูกแปลง:",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black),
            ),
            SizedBox(height: 5),
            _transformedSubtitle.isNotEmpty
                ? _buildColoredText(_transformedSubtitle)
                : Text("รอข้อมูล...", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green)),

            SizedBox(height: 20),

            // 🔹 ข้อความก่อนแปลง
            Text(
              "🔹 ข้อความก่อนแปลง:",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black),
            ),
            SizedBox(height: 5),
            Text(
              _previousSubtitle,
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 20),

            // 🔹 คำพูดปัจจุบัน
            Text(
              "🎤 คำพูดปัจจุบัน:",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black),
            ),
            SizedBox(height: 5),
            Text(
              _currentSubtitle.isEmpty ? "กำลังฟัง..." : _currentSubtitle,
              style: TextStyle(fontSize: 20, color: Colors.grey[700]),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
