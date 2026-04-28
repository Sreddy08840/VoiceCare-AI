import { useState, useEffect, useRef } from 'react';
import { Mic, Square, Activity, Calendar, Clock, User, Phone, CheckCircle, Clock3 } from 'lucide-react';
import './index.css';

function App() {
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [status, setStatus] = useState('Idle');
  const [transcripts, setTranscripts] = useState<{role: string, text: string}[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const [voiceSupported, setVoiceSupported] = useState({ stt: false, tts: false });

  const isSessionActiveRef = useRef(isSessionActive);
  
  useEffect(() => {
    isSessionActiveRef.current = isSessionActive;
  }, [isSessionActive]);

  useEffect(() => {
    fetchAppointments();
    
    // Check Compatibility
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const hasSTT = !!SpeechRecognition;
    const hasTTS = 'speechSynthesis' in window;
    setVoiceSupported({ stt: hasSTT, tts: hasTTS });

    if (hasSTT) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true; // Use interim for better UI feedback
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        console.log('STT: Started listening');
        setStatus('Listening...');
      };

      recognition.onresult = (event: any) => {
        const result = event.results[event.results.length - 1];
        if (result.isFinal) {
          const text = result[0].transcript;
          console.log('STT: Final transcript ->', text);
          simulateUserSpeech(text);
        } else {
          console.log('STT: Interim ->', result[0].transcript);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('STT Error:', event.error);
        if (event.error === 'not-allowed') {
          alert('Microphone permission denied. Please allow mic access in your browser settings.');
        } else if (event.error === 'network') {
          console.warn('STT Network Error. Please ensure you have an active internet connection, or if you are using Chrome, Google speech services might be temporarily unavailable or blocked.');
        }
        setStatus(`STT Error: ${event.error}`);
      };

      recognition.onend = () => {
        console.log('STT: Ended');
        if (isSessionActiveRef.current) {
          console.log('STT: Restarting...');
          // Add a small timeout to prevent tight infinite loop on persistent errors
          setTimeout(() => {
             if (isSessionActiveRef.current) {
               try { recognition.start(); } catch(e) {}
             }
          }, 1000);
        }
      };

      recognitionRef.current = recognition;
    }
  }, []); // Run only once on mount

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Basic language detection
      if (/[\u0900-\u097F]/.test(text)) utterance.lang = 'hi-IN';
      else if (/[\u0B80-\u0BFF]/.test(text)) utterance.lang = 'ta-IN';
      else utterance.lang = 'en-US';

      window.speechSynthesis.speak(utterance);
    }
  };

  const fetchAppointments = async () => {
    try {
      const res = await fetch('http://127.0.0.1:3001/api/appointments');
      if (res.ok) {
        const data = await res.json();
        setAppointments(data);
      }
    } catch (err) {
      console.error("Failed to fetch appointments", err);
    }
  };

  const toggleCall = () => {
    if (isSessionActive) {
      // Disconnect
      wsRef.current?.close();
      recognitionRef.current?.stop();
      window.speechSynthesis.cancel();
      setIsSessionActive(false);
      setStatus('Call ended');
      setTimeout(() => setStatus('Idle'), 3000);
    } else {
      // Connect to our Node.js API Gateway WebSocket
      setStatus('Connecting...');
      const wsUrl = 'ws://127.0.0.1:3001';
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.error('WS Connection timed out');
          setStatus('Connection Timeout - Check API Gateway');
          ws.close();
          setIsSessionActive(false);
        }
      }, 5000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        setIsSessionActive(true);
        setStatus('Listening...');
        recognitionRef.current?.start(); // Start listening
      };

      ws.onmessage = async (event) => {
        try {
          const raw = event.data instanceof Blob ? await event.data.text() : event.data;
          const msg = JSON.parse(raw);
          if (msg.type === 'agent_text' || msg.type === 'text') {
            setTranscripts(prev => [...prev, { role: 'agent', text: msg.text }]);
            setStatus('Speaking...');
            speakText(msg.text); // Speak aloud
            setTimeout(() => setStatus('Listening...'), 2000);
            if (msg.text.toLowerCase().includes('booked')) {
              fetchAppointments();
            }
          }
        } catch (e) {
          console.error('Error parsing WS message', e);
        }
      };

      ws.onclose = () => {
        setIsSessionActive(false);
        recognitionRef.current?.stop(); // Stop listening
        setStatus('Disconnected');
      };

      ws.onerror = (e) => {
        console.error('WebSocket Error:', e);
        setStatus('Error connecting');
        setIsSessionActive(false);
      };
    }
  };

  // Simulate user speaking
  const simulateUserSpeech = (text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setTranscripts(prev => [...prev, { role: 'user', text }]);
    wsRef.current.send(JSON.stringify({ type: 'user_text', text }));
    setStatus('Processing...');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex font-sans text-gray-900">
      {/* Sidebar / Dashboard */}
      <div className="w-1/3 bg-white border-r border-gray-200 p-6 overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 flex items-center text-blue-600">
          <Calendar className="mr-2" /> Appointments
        </h2>
        
        <div className="space-y-4">
          {appointments.length === 0 ? (
            <p className="text-gray-500 italic">No upcoming appointments.</p>
          ) : (
            appointments.map((apt, idx) => (
              <div key={idx} className="p-4 border border-gray-100 rounded-xl bg-gray-50 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg">{apt.patient_name}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${apt.status === 'booked' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {apt.status}
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-600 mb-1">
                  <User className="w-4 h-4 mr-2 text-gray-400" /> Dr. {apt.doctor_name}
                </div>
                <div className="flex items-center text-sm text-gray-600 mb-1">
                  <Calendar className="w-4 h-4 mr-2 text-gray-400" /> {new Date(apt.appointment_date).toLocaleDateString()}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Clock3 className="w-4 h-4 mr-2 text-gray-400" /> {apt.appointment_time}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Interaction Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 relative">
        <div className="absolute top-8 right-8 flex space-x-2">
          <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold">EN</span>
          <span className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-xs font-semibold">HI</span>
          <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-xs font-semibold">TA</span>
        </div>

        <div className="max-w-2xl w-full flex flex-col items-center">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">ClinicVoice AI</h1>
          <p className="text-gray-500 mb-12 text-center">Multilingual Voice Assistant for Clinical Appointments</p>

          {/* Voice Button */}
          <div className="relative mb-8">
            {isSessionActive && (
              <div className="absolute -inset-4 bg-blue-100 rounded-full animate-ping opacity-75"></div>
            )}
            <button 
              className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-xl
                ${isSessionActive 
                  ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-200' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-200'}`}
              onClick={toggleCall}
            >
              {isSessionActive ? <Square size={32} fill="currentColor" /> : <Mic size={36} />}
            </button>
          </div>

          <div className="flex flex-col items-center space-y-2 mb-8">
            <div className="flex items-center space-x-2 text-gray-600 font-medium">
              {isSessionActive && <Activity size={20} className="text-blue-600 animate-pulse" />}
              <span>{status}</span>
            </div>
            
            <div className="flex space-x-4 text-[10px] uppercase tracking-widest font-bold">
              <span className={voiceSupported.stt ? 'text-green-500' : 'text-red-500'}>
                STT: {voiceSupported.stt ? 'Available' : 'Missing'}
              </span>
              <span className={voiceSupported.tts ? 'text-green-500' : 'text-red-500'}>
                TTS: {voiceSupported.tts ? 'Available' : 'Missing'}
              </span>
              <button 
                onClick={() => speakText("Voice system test. Hello!")}
                className="text-blue-500 hover:underline"
              >
                Test Voice
              </button>
            </div>
          </div>

          {/* Quick Simulators for Testing Without Mic */}
          {isSessionActive && (
             <div className="w-full flex flex-wrap justify-center gap-2 mb-8">
               <button onClick={() => simulateUserSpeech("Book appointment tomorrow")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">1. Book tomorrow</button>
               <button onClick={() => simulateUserSpeech("Change my appointment to 5pm")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">2. Change to 5pm</button>
               <button onClick={() => simulateUserSpeech("I want an evening slot")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">3. Evening slot</button>
               <button onClick={() => simulateUserSpeech("कल की अपॉइंटमेंट बुक कर दो")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">4. Hindi test</button>
               <button onClick={() => simulateUserSpeech("நாளை ஒரு அப்பாயிண்ட்மெண்ட் வேண்டும்")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">5. Tamil test</button>
               <button onClick={() => simulateUserSpeech("Book with Dr. Rao tomorrow at 8 AM")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">6. Conflict test</button>
               <button onClick={() => simulateUserSpeech("Can you order me a pizza?")} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition font-medium">7. Random input</button>
             </div>
          )}

          {/* Live Transcription */}
          <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-64 overflow-y-auto">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Live Transcription</h3>
            <div className="space-y-4">
              {transcripts.length === 0 ? (
                <p className="text-gray-400 text-center italic mt-12">Conversation will appear here...</p>
              ) : (
                transcripts.map((t, i) => (
                  <div key={i} className={`flex ${t.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                      t.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-br-none' 
                        : 'bg-gray-100 text-gray-800 rounded-bl-none'
                    }`}>
                      <p className="text-[15px]">{t.text}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
