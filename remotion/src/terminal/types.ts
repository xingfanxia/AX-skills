/**
 * Terminal-session event model. A promo is a scripted Claude Code session:
 * the user invokes the skill, the agent works, output streams back. The engine
 * computes all timing deterministically from the events (no per-event frames in
 * the data) so authoring a session is pure content.
 */
export type TermEvent =
  | {k: 'in'; text: string}                       // prompt line: ❯ <text>, typed out
  | {k: 'sys'; text: string}                      // dim system / comment line (instant)
  | {k: 'run'; text: string; sec?: number}        // spinner for sec, then ✓, persists
  | {k: 'out'; lines: string[]; accent?: boolean} // output block, streamed line by line
  | {k: 'done'; text: string};                    // highlighted result line

export type Session = {
  /** composition id === deck slug === R2 filename */
  id: string;
  /** shown in the title bar after "claude — " */
  title: string;
  /** small caption under the window */
  caption: string;
  events: TermEvent[];
};

export const FPS = 30;

// How many rendered lines each event occupies (for autoscroll math).
export function eventLineCount(e: TermEvent): number {
  switch (e.k) {
    case 'out':
      return e.lines.length;
    default:
      return 1;
  }
}

// Duration in frames for an event, derived from its content.
export function eventFrames(e: TermEvent): number {
  switch (e.k) {
    case 'in':
      return Math.ceil(e.text.length * 1.7) + 18;
    case 'sys':
      return 11;
    case 'run':
      return Math.round((e.sec ?? 1) * FPS) + 12;
    case 'out':
      return e.lines.length * 9 + 16;
    case 'done':
      return 40;
  }
}

export type Timed = {e: TermEvent; start: number; dur: number; lineStart: number};

/** Lay events on a frame timeline + track cumulative line index for scrolling. */
export function layout(events: TermEvent[]): {timed: Timed[]; total: number} {
  let f = 0;
  let line = 0;
  const timed = events.map((e) => {
    const dur = eventFrames(e);
    const t: Timed = {e, start: f, dur, lineStart: line};
    f += dur;
    line += eventLineCount(e);
    return t;
  });
  return {timed, total: f};
}
