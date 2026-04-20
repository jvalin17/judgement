import { render, screen } from "@testing-library/react";
import { PlayerSeat } from "./OpponentArea";
import { makePlayer } from "../../test/helpers";
import { SettingsProvider } from "../../context/SettingsContext";

function renderSeat(props: Parameters<typeof PlayerSeat>[0]) {
  return render(
    <SettingsProvider>
      <PlayerSeat {...props} />
    </SettingsProvider>
  );
}

const defaultProps = {
  position: { left: "50%", top: "20%" },
  isCurrentTurn: false,
  bid: null as number | null,
  tricksWon: 0,
  score: 0,
  cardsRemaining: 3,
};

describe("PlayerSeat", () => {
  it("shows dash when no bid placed", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps });
    const badge = screen.getByTestId("seat-Bot1");
    expect(badge).toHaveTextContent("\u2014");
  });

  it("shows won/bid status in top half", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, bid: 3, tricksWon: 1 });
    const badge = screen.getByTestId("seat-Bot1");
    const top = badge.querySelector(".statBadgeTop");
    expect(top).toHaveTextContent("1/3");
  });

  it("shows score in bottom half", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, bid: 2, tricksWon: 2, score: 42 });
    const badge = screen.getByTestId("seat-Bot1");
    const bottom = badge.querySelector(".statBadgeBottom");
    expect(bottom).toHaveTextContent("42");
  });

  it("applies active class when it is the player's turn", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, isCurrentTurn: true });
    const badge = screen.getByTestId("seat-Bot1");
    expect(badge.className).toContain("statBadgeActive");
  });

  it("does not apply active class when not the player's turn", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, isCurrentTurn: false });
    const badge = screen.getByTestId("seat-Bot1");
    expect(badge.className).not.toContain("statBadgeActive");
  });

  it("shows NOW pill when it is the player's turn", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, isCurrentTurn: true });
    expect(screen.getByText("NOW")).toBeInTheDocument();
  });

  it("shows player name", () => {
    renderSeat({ player: makePlayer({ name: "Jalebi" }), ...defaultProps });
    expect(screen.getByText("Jalebi")).toBeInTheDocument();
  });

  it("shows 0/0 when bid is zero and no tricks won", () => {
    renderSeat({ player: makePlayer({ name: "Bot1" }), ...defaultProps, bid: 0, tricksWon: 0 });
    const top = screen.getByTestId("seat-Bot1").querySelector(".statBadgeTop");
    expect(top).toHaveTextContent("0/0");
  });
});

describe("Seat layout positions", () => {
  it("no seat overlaps the top-left round info corner", async () => {
    // Round info is positioned at top-left (top: 8px, left: 8px).
    // Seats near the top-left corner (left < 20% AND top < 15%) would overlap.
    const layouts: Record<number, Array<{ left: string; top: string }>> = {
      3: [
        { left: "50%", top: "82%" },
        { left: "15%", top: "30%" },
        { left: "85%", top: "30%" },
      ],
      4: [
        { left: "50%", top: "82%" },
        { left: "10%", top: "45%" },
        { left: "50%", top: "10%" },
        { left: "90%", top: "45%" },
      ],
      5: [
        { left: "50%", top: "82%" },
        { left: "8%", top: "45%" },
        { left: "25%", top: "12%" },
        { left: "75%", top: "12%" },
        { left: "92%", top: "45%" },
      ],
      6: [
        { left: "50%", top: "82%" },
        { left: "8%", top: "45%" },
        { left: "25%", top: "12%" },
        { left: "50%", top: "8%" },
        { left: "75%", top: "12%" },
        { left: "92%", top: "45%" },
      ],
    };

    for (const [, seats] of Object.entries(layouts)) {
      for (let seatIndex = 1; seatIndex < seats.length; seatIndex++) {
        const topPercent = parseFloat(seats[seatIndex].top);
        const leftPercent = parseFloat(seats[seatIndex].left);
        // No seat should be in the top-left corner where round info lives
        const overlapsRoundInfo = leftPercent < 20 && topPercent < 15;
        expect(overlapsRoundInfo).toBe(false);
      }
    }
  });
});
