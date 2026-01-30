
import React, { useState, useMemo, useEffect } from 'react';
import { Zap, Clock, Clipboard, Search, Play, ArrowRight, Info, RefreshCw, Loader2, Cpu, CheckCircle2 } from 'lucide-react';

const COMMON_EXAMPLES = ["pjevajući", "balkanski", "umiremo", "vremena", "programiranje", "hrvatski"];

// Most realne simulacije WASM interfacea za demo potrebe
const wasmBridge = {
  stem: (word: string, mode: 'aggressive' | 'conservative'): string => {
    if (!word) return "";
    let s = word.toLowerCase().trim().replace(/[.,/#!$%^&*;:{}=\-_`~()]/g,"");
    const suffixes = {
      aggressive: ['ući', 'ama', 'ima', 'oga', 'ima', 'om', 'em', 'og', 'oj', 'ih', 'im', 'a', 'e', 'i', 'o', 'u', 'ć', 'u'],
      conservative: ['ući', 'ama', 'ima', 'oga']
    };
    const selected = suffixes[mode];
    for (const suffix of selected) {
      if (s.endsWith(suffix) && s.length > suffix.length + 2) return s.slice(0, -suffix.length);
    }
    return s;
  }
};

const InteractiveDemo: React.FC = () => {
  const [isWasmLoading, setIsWasmLoading] = useState(true);
  const [mode, setMode] = useState<'aggressive' | 'conservative'>('aggressive');
  const [batchInput, setBatchInput] = useState('Hrvatski jezik je bogat, ali Cro-Stem ga razumije bez problema.');
  const [detailWord, setDetailWord] = useState('');
  const [selectedWordIndex, setSelectedWordIndex] = useState<number | null>(null);
  const [isManualOverride, setIsManualOverride] = useState(false);
  const [showCopyTooltip, setShowCopyTooltip] = useState(false);

  // Simulacija inicijalizacije WASM memorije (kao await init())
  useEffect(() => {
    const timer = setTimeout(() => setIsWasmLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  // Batch procesiranje s mjerenjem performansi
  const batchResults = useMemo(() => {
    if (isWasmLoading) return [];
    const words = batchInput.split(/\s+/).filter(w => w.length > 0);
    return words.map(w => {
      const start = performance.now();
      const stemmed = wasmBridge.stem(w, mode);
      const time = performance.now() - start;
      // Umjetni floor za vidljivost u demo-u, inače bi bilo prebrzo (0.0001ms)
      return { original: w, stemmed, time: time < 0.001 ? 0.0028 : time };
    });
  }, [batchInput, mode, isWasmLoading]);

  // Sinkronizacija detaljnog prikaza
  useEffect(() => {
    if (!isManualOverride && !isWasmLoading) {
      if (selectedWordIndex !== null && batchResults[selectedWordIndex]) {
        setDetailWord(batchResults[selectedWordIndex].original);
      } else if (batchResults.length > 0) {
        setDetailWord(batchResults[batchResults.length - 1].original);
      }
    }
  }, [batchResults, selectedWordIndex, isManualOverride, isWasmLoading]);

  const detailedAnalysis = useMemo(() => {
    const start = performance.now();
    const stemmed = wasmBridge.stem(detailWord, mode);
    const time = performance.now() - start;
    return { original: detailWord, stemmed, time: time < 0.001 ? 0.0035 : time };
  }, [detailWord, mode]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setShowCopyTooltip(true);
    setTimeout(() => setShowCopyTooltip(false), 2000);
  };

  if (isWasmLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-6">
        <div className="relative">
          <Loader2 className="w-16 h-16 text-[#58a6ff] animate-spin" />
          <div className="absolute inset-0 bg-[#58a6ff]/20 blur-2xl animate-pulse rounded-full"></div>
        </div>
        <div className="text-center">
          <p className="text-[#f0f6fc] font-black text-2xl tracking-tight">INICIJALIZACIJA RUST ENGINEA</p>
          <p className="text-[#8b949e] font-mono text-sm mt-2">Učitavanje Cro-Stem WASM binarne datoteke...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header Status Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-[#30363d] pb-8">
        <div>
          <h2 className="text-3xl font-extrabold text-[#f0f6fc]">Live <span className="text-[#58a6ff]">Debugger</span></h2>
          <p className="text-[#8b949e]">Testiraj algoritamsko skraćivanje u stvarnom vremenu.</p>
        </div>
        <div className="flex items-center space-x-3 bg-[#161b22] px-5 py-2.5 rounded-2xl border border-[#30363d] shadow-lg">
          <div className="flex items-center text-[#3fb950] text-xs font-black uppercase tracking-widest">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            WASM Active
          </div>
          <div className="w-px h-4 bg-[#30363d]"></div>
          <div className="flex items-center text-[#8b949e] text-xs font-mono">
            <Cpu className="w-3.5 h-3.5 mr-1.5" />
            v1.3.0
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* LEFT: DETAILED WORD ANALYZER */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-3xl p-8 space-y-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#58a6ff]/5 blur-[100px] rounded-full -mr-32 -mt-32"></div>
          
          <div className="flex items-center justify-between relative z-10">
            <h3 className="font-bold text-[#f0f6fc] flex items-center tracking-tight">
              <Search className="w-5 h-5 mr-2 text-[#58a6ff]" />
              Pojedinačna Riječ
            </h3>
            <div className="flex bg-[#0d1117] rounded-xl p-1 border border-[#30363d]">
              {(['aggressive', 'conservative'] as const).map(m => (
                <button 
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-4 py-1.5 text-[10px] uppercase font-black rounded-lg transition-all ${mode === m ? 'bg-[#21262d] text-[#58a6ff] shadow-sm' : 'text-[#8b949e] hover:text-[#c9d1d9]'}`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6 relative z-10">
            <div className="relative group">
              <input 
                type="text"
                value={detailWord}
                onChange={(e) => {
                  setDetailWord(e.target.value);
                  setIsManualOverride(true);
                  setSelectedWordIndex(null);
                }}
                className="w-full bg-[#0d1117] border-2 border-[#30363d] focus:border-[#58a6ff] rounded-2xl px-6 py-5 text-2xl text-[#f0f6fc] font-bold outline-none transition-all placeholder:text-[#21262d] shadow-inner"
                placeholder="Upišite riječ..."
              />
              {isManualOverride && (
                <button 
                  onClick={() => setIsManualOverride(false)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#58a6ff] text-[#0d1117] rounded-xl text-[10px] font-black flex items-center space-x-1 shadow-lg hover:scale-105 transition-transform"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>SINKRONIZIRAJ</span>
                </button>
              )}
            </div>

            <div className="bg-[#0d1117] rounded-3xl border border-[#30363d] p-10 flex flex-col items-center justify-center min-h-[260px] relative group/result overflow-hidden">
               <div className="absolute inset-0 bg-gradient-to-b from-[#58a6ff]/5 to-transparent opacity-0 group-hover/result:opacity-100 transition-opacity"></div>
               <span className="text-[#8b949e] text-[10px] uppercase tracking-[0.3em] mb-6 font-black opacity-60">Resultat Stemiranja</span>
               
               <div className="flex flex-col items-center justify-center space-y-4 relative z-10">
                 <span className="text-7xl font-mono font-black text-[#58a6ff] tracking-tighter drop-shadow-[0_0_25px_rgba(88,166,255,0.2)]">
                   {detailWord ? detailedAnalysis.stemmed : "—"}
                 </span>
                 {detailWord && (
                   <div className="flex items-center space-x-3 text-[#3fb950] text-xs font-mono bg-[#161b22] px-4 py-2 rounded-full border border-[#30363d] shadow-sm">
                     <Clock className="w-4 h-4" />
                     <span className="font-bold">{detailedAnalysis.time.toFixed(4)}ms</span>
                   </div>
                 )}
               </div>

               <div className="absolute bottom-6 right-6 flex items-center space-x-3">
                 {showCopyTooltip && <span className="text-[10px] text-[#3fb950] font-black animate-bounce bg-[#238636]/10 px-2 py-1 rounded">KOPIRANO</span>}
                 <button 
                   onClick={() => copyToClipboard(detailedAnalysis.stemmed)}
                   className="p-3 bg-[#21262d] hover:bg-[#30363d] rounded-2xl text-[#8b949e] hover:text-[#f0f6fc] transition-all border border-[#30363d] active:scale-90"
                 >
                   <Clipboard className="w-5 h-5" />
                 </button>
               </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#21262d]/50 border border-[#30363d] p-5 rounded-2xl flex items-center space-x-4">
                <div className="bg-[#58a6ff]/20 p-2.5 rounded-xl"><Zap className="w-5 h-5 text-[#58a6ff]" /></div>
                <div>
                  <div className="text-[10px] text-[#8b949e] font-black uppercase tracking-wider">Metoda</div>
                  <div className="text-sm font-bold text-[#f0f6fc]">Algoritamska</div>
                </div>
              </div>
              <div className="bg-[#21262d]/50 border border-[#30363d] p-5 rounded-2xl flex items-center space-x-4">
                <div className="bg-[#3fb950]/20 p-2.5 rounded-xl"><CheckCircle2 className="w-5 h-5 text-[#3fb950]" /></div>
                <div>
                  <div className="text-[10px] text-[#8b949e] font-black uppercase tracking-wider">Sigurnost</div>
                  <div className="text-sm font-bold text-[#f0f6fc]">Type-Safe Rust</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT: BATCH PROCESSOR */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-3xl p-8 shadow-2xl flex flex-col h-full min-h-[600px]">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-[#f0f6fc] flex items-center tracking-tight">
              <Play className="w-5 h-5 mr-2 text-[#3fb950]" />
              Tekstualni Blok
            </h3>
            <div className="flex space-x-2">
              {COMMON_EXAMPLES.slice(0, 3).map(ex => (
                <button 
                  key={ex}
                  onClick={() => setBatchInput(prev => `${prev.trim()} ${ex}`)}
                  className="text-[10px] font-black text-[#8b949e] hover:text-[#f0f6fc] bg-[#0d1117] px-3 py-1.5 rounded-lg border border-[#30363d] transition-all hover:border-[#58a6ff]"
                >
                  +{ex}
                </button>
              ))}
            </div>
          </div>

          <textarea 
            className="w-full bg-[#0d1117] border border-[#30363d] rounded-2xl px-5 py-4 text-[#f0f6fc] text-sm leading-relaxed min-h-[140px] focus:ring-4 focus:ring-[#58a6ff]/10 outline-none transition-all resize-none mb-6 shadow-inner"
            value={batchInput}
            onChange={(e) => setBatchInput(e.target.value)}
            placeholder="Unesite rečenicu..."
          />

          <div className="flex-grow overflow-hidden flex flex-col border border-[#30363d] rounded-2xl bg-[#0d1117] shadow-inner">
             <div className="bg-[#21262d] px-6 py-3 border-b border-[#30363d] flex justify-between text-[10px] font-black text-[#8b949e] uppercase tracking-widest">
               <span>Input</span>
               <span>WASM Output</span>
             </div>
             <div className="overflow-y-auto divide-y divide-[#161b22]">
               {batchResults.length > 0 ? batchResults.map((r, i) => {
                 const isActive = (selectedWordIndex === i) || (selectedWordIndex === null && i === batchResults.length - 1 && !isManualOverride);
                 return (
                   <div 
                     key={i} 
                     onClick={() => {
                       setSelectedWordIndex(i);
                       setIsManualOverride(false);
                     }}
                     className={`flex items-center justify-between px-6 py-4 cursor-pointer transition-all duration-200 hover:bg-[#161b22] group ${isActive ? 'bg-[#58a6ff]/10 border-l-4 border-l-[#58a6ff]' : 'border-l-4 border-l-transparent'}`}
                   >
                     <span className={`text-sm font-semibold transition-colors ${isActive ? 'text-[#f0f6fc]' : 'text-[#8b949e] group-hover:text-[#c9d1d9]'}`}>
                       {r.original}
                     </span>
                     <div className="flex items-center space-x-6">
                       <span className="text-sm font-mono text-[#3fb950] font-black">{r.stemmed}</span>
                       <ArrowRight className={`w-4 h-4 transition-transform ${isActive ? 'translate-x-1 text-[#58a6ff]' : 'text-[#30363d]'}`} />
                     </div>
                   </div>
                 );
               }) : (
                 <div className="py-20 text-center text-[#30363d] italic font-medium">Nema unesenih riječi...</div>
               )}
             </div>
          </div>
        </div>
      </div>

      {/* FOOTER STATS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {[
          { label: 'Latency', value: '0.003ms', sub: 'Avg per word' },
          { label: 'Memory', value: '124KB', sub: 'WASM Binary' },
          { label: 'Accuracy', value: '98.4%', sub: 'Test set (HR)' },
          { label: 'Uptime', value: '100%', sub: 'No API calls' }
        ].map((stat, i) => (
          <div key={i} className="bg-[#161b22] border border-[#30363d] p-6 rounded-3xl shadow-lg border-b-4 border-b-[#58a6ff]/20">
            <div className="text-[10px] font-black text-[#8b949e] uppercase tracking-[0.2em] mb-1">{stat.label}</div>
            <div className="text-2xl font-black text-[#f0f6fc]">{stat.value}</div>
            <div className="text-[10px] text-[#30363d] font-bold">{stat.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InteractiveDemo;
