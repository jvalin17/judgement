/**
 * Pip positions for number cards 2-10.
 * Coordinates are percentages (0-100) from top-left of the pip area.
 * Matches the standard playing card pip arrangements.
 */

export interface PipPosition {
  x: number;
  y: number;
  inverted?: boolean;
}

const COL_LEFT = 28;
const COL_CENTER = 50;
const COL_RIGHT = 72;

const ROW_1 = 10;
const ROW_2 = 30;
const ROW_MID_HIGH = 35;
const ROW_CENTER = 50;
const ROW_MID_LOW = 65;
const ROW_4 = 70;
const ROW_5 = 90;

export const PIP_LAYOUTS: Record<number, PipPosition[]> = {
  2: [
    { x: COL_CENTER, y: ROW_1 },
    { x: COL_CENTER, y: ROW_5, inverted: true },
  ],
  3: [
    { x: COL_CENTER, y: ROW_1 },
    { x: COL_CENTER, y: ROW_CENTER },
    { x: COL_CENTER, y: ROW_5, inverted: true },
  ],
  4: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  5: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_CENTER, y: ROW_CENTER },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  6: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_LEFT, y: ROW_CENTER },
    { x: COL_RIGHT, y: ROW_CENTER },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  7: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_CENTER, y: ROW_MID_HIGH },
    { x: COL_LEFT, y: ROW_CENTER },
    { x: COL_RIGHT, y: ROW_CENTER },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  8: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_CENTER, y: ROW_MID_HIGH },
    { x: COL_LEFT, y: ROW_CENTER },
    { x: COL_RIGHT, y: ROW_CENTER },
    { x: COL_CENTER, y: ROW_MID_LOW },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  9: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_LEFT, y: ROW_2 },
    { x: COL_RIGHT, y: ROW_2 },
    { x: COL_CENTER, y: ROW_CENTER },
    { x: COL_LEFT, y: ROW_4, inverted: true },
    { x: COL_RIGHT, y: ROW_4, inverted: true },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
  10: [
    { x: COL_LEFT, y: ROW_1 },
    { x: COL_RIGHT, y: ROW_1 },
    { x: COL_LEFT, y: ROW_2 },
    { x: COL_RIGHT, y: ROW_2 },
    { x: COL_CENTER, y: ROW_MID_HIGH },
    { x: COL_CENTER, y: ROW_MID_LOW, inverted: true },
    { x: COL_LEFT, y: ROW_4, inverted: true },
    { x: COL_RIGHT, y: ROW_4, inverted: true },
    { x: COL_LEFT, y: ROW_5, inverted: true },
    { x: COL_RIGHT, y: ROW_5, inverted: true },
  ],
};
