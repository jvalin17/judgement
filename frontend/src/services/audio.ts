/**
 * Celebratory sound effects using the Web Audio API.
 * No audio files — everything is synthesized on the fly.
 */

let audioContext: AudioContext | null = null;

function getContext(): AudioContext | null {
  try {
    if (!audioContext) {
      audioContext = new AudioContext();
    }
    return audioContext;
  } catch {
    return null; // no audio support
  }
}

function playTone(
  ctx: AudioContext,
  frequency: number,
  startTime: number,
  duration: number,
  volume: number,
  type: OscillatorType = "sine",
) {
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();

  oscillator.type = type;
  oscillator.frequency.value = frequency;

  gain.gain.setValueAtTime(0, startTime);
  gain.gain.linearRampToValueAtTime(volume, startTime + 0.02);
  gain.gain.setValueAtTime(volume, startTime + duration * 0.6);
  gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);

  oscillator.connect(gain);
  gain.connect(ctx.destination);

  oscillator.start(startTime);
  oscillator.stop(startTime + duration);
}

/**
 * Short ascending fanfare — plays when you win (1st place).
 * ~1.2 seconds, cheerful major chord arpeggio.
 */
export function playVictorySound() {
  const ctx = getContext();
  if (!ctx) return;

  const now = ctx.currentTime;
  const notes = [523, 659, 784, 1047]; // C5 E5 G5 C6
  const volume = 0.15;

  notes.forEach((freq, index) => {
    playTone(ctx, freq, now + index * 0.15, 0.4, volume, "triangle");
    // subtle harmonic layer
    playTone(ctx, freq * 1.5, now + index * 0.15, 0.25, volume * 0.3, "sine");
  });

  // final shimmer chord
  playTone(ctx, 1047, now + 0.7, 0.6, volume * 0.8, "sine");
  playTone(ctx, 1319, now + 0.7, 0.6, volume * 0.5, "sine");
  playTone(ctx, 1568, now + 0.7, 0.6, volume * 0.3, "sine");
}

/**
 * Gentler sound for 2nd/3rd place — warm ascending notes.
 */
export function playGoodGameSound() {
  const ctx = getContext();
  if (!ctx) return;

  const now = ctx.currentTime;
  const notes = [392, 494, 587]; // G4 B4 D5
  const volume = 0.12;

  notes.forEach((freq, index) => {
    playTone(ctx, freq, now + index * 0.18, 0.35, volume, "triangle");
  });
}
