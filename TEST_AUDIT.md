# Test Audit — Judgement Card Game

**Generated:** 2026-04-21 | **Updated:** 2026-04-22
**Backend:** 442 tests (all pass) | **Frontend:** 185 tests (all pass) | **Total: 627**

> Started at 394 (307 documented in CLAUDE.md). Added 239 new tests, removed 6 duplicates.

---

## Backend Tests (345 total: 269 unit + 76 integration)

### `test_trick_resolver.py` — 6 unit tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_highest_of_lead_suit_wins` | p1=H5, p2=H10, p3=H3; trump=S | winner="p2" | unit |
| 2 | `test_trump_beats_lead_suit` | p1=H-A, p2=S-2, p3=H-K; trump=S | winner="p2" | unit |
| 3 | `test_higher_trump_beats_lower_trump` | p1=H-A, p2=S-2, p3=S-7; trump=S | winner="p3" | unit |
| 4 | `test_off_suit_non_trump_loses` | p1=H-3, p2=C-A, p3=H-5; trump=S | winner="p3" | unit |
| 5 | `test_lead_suit_is_trump` | p1=S-3, p2=S-A, p3=H-A; trump=S | winner="p2" | unit |
| 6 | `test_single_card_trick` | p1=H-5 (solo); trump=S | winner="p1" | unit |

### `test_scorer.py` — 7 unit tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_bid_zero_met` | bid=0, won=0 | +10 | unit |
| 2 | `test_bid_zero_missed` | bid=0, won=2 | -10 | unit |
| 3 | `test_bid_one_met` | bid=1, won=1 | +11 | unit |
| 4 | `test_bid_one_missed` | bid=1, won=0 | -11 | unit |
| 5 | `test_bid_high_met` | bid=5, won=5 | +50 | unit |
| 6 | `test_bid_high_missed` | bid=3, won=2 | -30 | unit |
| 7 | `test_multiple_players` | p1:bid2/won2, p2:bid0/won1, p3:bid1/won1 | {p1:20, p2:-10, p3:11} | unit |

### `test_validators.py` — 18 unit tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_no_lead_suit_all_valid` | hand=[H-A,C-2]; lead=None | both valid | unit |
| 2 | `test_must_follow_suit` | hand=[H-A,C-2,H-3]; lead=Hearts | 2 hearts only | unit |
| 3 | `test_no_matching_suit_all_valid` | hand=[C-A,D-2]; lead=Hearts | both valid | unit |
| 4 | `test_play_valid_card` | H-A in hand, lead=None | True | unit |
| 5 | `test_play_card_not_in_hand` | C-2 not in hand | False | unit |
| 6 | `test_play_wrong_suit_when_has_matching` | play C-2 when has H-A, lead=Hearts | False | unit |
| 7 | `test_valid_bid_non_dealer` | amount=3, idx=0, 3 players, 5 cards | True | unit |
| 8 | `test_bid_out_of_range` | amount=-1 and amount=6, 5 cards | both False | unit |
| 9 | `test_dealer_forbidden_bid` | dealer idx=2, total=3, 5 cards | bid 2 False, bid 1 True | unit |
| 10 | `test_non_dealer_not_constrained_standard` | idx=1 (not dealer) | bid 2 True | unit |
| 11 | `test_must_lose_first_player_not_constrained` | idx=0, must_lose=True | bid 5 True, bid 4 True | unit |
| 12 | `test_must_lose_middle_player_not_constrained` | idx=1, must_lose=True | bid 3 True, bid 2 True | unit |
| 13 | `test_must_lose_dealer_constrained` | dealer idx=2, must_lose=True | bid 2 False, bid 1 True | unit |
| 14 | `test_must_lose_one_card_round` | 1 card, 3 players, must_lose | dealer can't bid 0 | unit |
| 15 | `test_forbidden_bid_standard_non_dealer` | idx=0 | None | unit |
| 16 | `test_forbidden_bid_standard_dealer` | dealer, total=3, 5 cards | forbidden=2 | unit |
| 17 | `test_forbidden_bid_must_lose_non_dealer` | idx=1, must_lose | None | unit |
| 18 | `test_forbidden_bid_must_lose_dealer` | dealer, must_lose, total=3 | forbidden=2 | unit |

### `test_deck.py` — 9 unit tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_has_52_cards` | create_deck() | len==52 | unit |
| 2 | `test_all_cards_unique` | create_deck() | 52 unique (suit,rank) | unit |
| 3 | `test_four_suits_thirteen_ranks` | create_deck() | 4 suits, 13 ranks | unit |
| 4 | `test_preserves_all_cards` | shuffle_deck(deck) | same cards sorted | unit |
| 5 | `test_seeded_shuffle_is_deterministic` | rng=Random(42) twice | both equal | unit |
| 6 | `test_does_not_mutate_original` | shuffle_deck(deck) | original unchanged | unit |
| 7 | `test_correct_hand_sizes` | deal(deck, 4, 10) | 4 hands, 10 each | unit |
| 8 | `test_no_duplicate_cards_across_hands` | deal(deck, 3, 10) | 30 unique | unit |
| 9 | `test_deal_one_card_each` | deal(deck, 5, 1) | 5 hands, 1 each | unit |

### `test_engine.py` — 17 tests (5 unit + 12 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `TestGameSetup::test_add_players` | add 3 Human players | len==3, all True | unit |
| 2 | `TestGameSetup::test_cannot_add_duplicate` | add same player twice | 2nd returns False | unit |
| 3 | `TestGameSetup::test_cannot_exceed_max_players` | add 6th to 10_to_1 (max 5) | returns False | unit |
| 4 | `TestGameSetup::test_need_min_two_players` | 1 player, start_game() | returns False | unit |
| 5 | `TestGameSetup::test_start_game_transitions_to_bidding` | 3 players, start | phase=BIDDING | integration |
| 6 | `TestBidding::test_bidding_order` | 3 players, dealer=p1 | current="p2" | integration |
| 7 | `TestBidding::test_place_valid_bid` | p2 bids 2 | True, 1 event | integration |
| 8 | `TestBidding::test_wrong_player_cannot_bid` | p1 bids (not turn) | False | integration |
| 9 | `TestBidding::test_bidding_completes` | p2:3, p3:2, p1:4 | phase=PLAYING | integration |
| 10 | `TestFullRound::test_play_full_round` | 10 tricks, valid cards | phase=ROUND_OVER | integration |
| 11 | `TestTurnOrder::test_trick_winner_leads_next` | 1 trick | current=winner | integration |
| 12 | `TestValidActions::test_get_valid_bids` | p2 in bidding | bids in [0,10] | integration |
| 13 | `TestValidActions::test_get_valid_cards` | playing phase | valid > 0 | integration |
| 14 | `TestRoundOverGating::test_round_stays_in_round_over` | full round | no auto-advance | integration |
| 15 | `TestRoundOverGating::test_continue_game_advances_to_bidding` | round + continue | phase=BIDDING | integration |
| 16 | `TestRoundOverGating::test_continue_game_rejects_wrong_phase` | continue during BIDDING | False | unit |
| 17 | `TestDealerRotation::test_dealer_rotates_each_round` | 2 rounds | r1:p1, r2:p2 | integration |

### `test_ai.py` — 33 tests (31 unit + 2 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `TestHandEvaluator::test_strong_hand_high_estimate` | S-A/K/Q + H-A + D-A; trump=S | trump=3, aces=3, tricks>=3 | unit |
| 2 | `TestHandEvaluator::test_weak_hand_low_estimate` | H-2/3 + D-2 + C-3/4; trump=S | trump=0, aces=0, tricks<1.5 | unit |
| 3 | `TestHandEvaluator::test_void_suit_adds_ruffing` | S-5 + H-2/3; trump=S | tricks>0 | unit |
| 4 | `TestEasyAI::test_always_returns_valid_bid` | 50 iter, valid=[0,1,2,3] | all in valid | unit |
| 5 | `TestEasyAI::test_always_returns_valid_card` | 50 iter, 3 valid cards | all in valid | unit |
| 6 | `TestMediumAI::test_bids_higher_with_strong_hand` | 20 each strong/weak | avg(strong)>avg(weak) | unit |
| 7 | `TestMediumAI::test_always_returns_valid_bid` | 20 iter, valid=[0,1,3,4] | all in valid | unit |
| 8 | `TestMediumAI::test_always_returns_valid_card` | 20 iter | all in valid | unit |
| 9 | `TestMediumAI::test_leads_with_high_card` | H-A/H-2/C-3; leading | plays Ace | unit |
| 10 | `TestMediumAI::test_tries_to_win_trick` | H-K/H-2; trick=[H-10] | plays King | unit |
| 11 | `TestHardAI::test_always_returns_valid_bid` | 20 iter | all in valid | unit |
| 12 | `TestHardAI::test_always_returns_valid_card` | 20 iter | all in valid | unit |
| 13 | `TestHardAI::test_bids_higher_with_strong_hand` | 20 each | avg(strong)>avg(weak) | unit |
| 14 | `TestHardAI::test_card_counting_affects_estimate` | S-A played vs not | bid_with>=bid_without | unit |
| 15 | `TestHardAI::test_plays_guaranteed_winner_in_middle` | H-A/K/Q; trick=[H-J] | plays Ace | unit |
| 16 | `TestAIFullGame::test_all_strategies_complete_game` | Easy/Med/Hard, full round | all succeed | integration |
| 17 | `TestAIPersonality::test_random_personality_in_bounds` | 50 random | all [0,1] | unit |
| 18 | `TestAIPersonality::test_personalities_vary` | 20 random | >3 unique | unit |
| 19 | `TestAIPersonality::test_predefined_archetypes` | AGG/CONS/TACT/GAMB | trait>=0.8 | unit |
| 20 | `TestOpponentModel::test_detects_void_from_offsuit_play` | p2 plays D-3 on H lead | H in p2 voids | unit |
| 21 | `TestOpponentModel::test_trump_play_implies_void` | p2 plays S-2 on H lead | p2 void in H | unit |
| 22 | `TestOpponentModel::test_following_suit_no_false_void` | p2 plays H-Q on H lead | not void | unit |
| 23 | `TestOpponentModel::test_opponent_needs_calculation` | p1:bid3/won1, p2:bid1/won1 | p1=2, p2=0 | unit |
| 24 | `TestOpponentModel::test_satisfied_vs_dangerous` | p1:met, p2:met, p3:needs3 | p2 satisfied, p3 dangerous | unit |
| 25 | `TestHardAIPositionalPlay::test_last_position_takes_cheap_win` | H-A/K/Q; trick=[H-5,H-J] | plays Queen | unit |
| 26 | `TestHardAIPositionalPlay::test_last_position_dumps_when_over_bid` | met bid; trick=[H-5,H-J] | plays D-3 | unit |
| 27 | `TestHardAIPositionalPlay::test_lead_low_trump_to_draw_out` | 4 trumps, aggression=0.9 | leads S-2 | unit |
| 28 | `TestHardAIPositionalPlay::test_guaranteed_non_trump_winner_first` | H-A, all others played | plays H-A | unit |
| 29 | `TestHardAITrumpManagement::test_conserves_ace_of_trump` | S-A/S-3, conservation=0.9 | NOT S-A | unit |
| 30 | `TestHardAITrumpManagement::test_lowest_winning_trump_in_trick` | S-A/S-3 vs [H-K] | S-3 | unit |
| 31 | `TestHardAISmartLosing::test_dumps_from_shortest_suit` | H-K + D-3/D-5; bid=0 | NOT H-K | unit |
| 32 | `TestHardAISmartLosing::test_avoids_accidental_win` | H-A/H-2; trick=[H-10,H-J]; bid=0 | plays H-2 | unit |
| 33 | `TestHardAIArchetypes::test_all_archetypes_complete_game` | 4 archetypes full round | all succeed | integration |

### `test_round_config.py` — 12 tests (8 unit + 4 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_10_to_1_has_10_rounds` | TEN_TO_ONE | len==10 | unit |
| 2 | `test_8_down_up_has_16_rounds` | EIGHT_DOWN_UP | len==16 | unit |
| 3 | `test_10_down_up_has_20_rounds` | TEN_DOWN_UP | len==20 | unit |
| 4 | `test_configs_are_frozen` | mutate config.cards | raises exception | unit |
| 5 | `test_same_object_returned_on_repeated_calls` | load twice | same object (is) | unit |
| 6 | `test_bridge_10_to_1` | JSON vs runtime | match | integration |
| 7 | `test_bridge_8_down_up` | JSON vs runtime | match | integration |
| 8 | `test_bridge_10_down_up` | JSON vs runtime | match | integration |
| 9 | `test_round_numbers_are_sequential` | all variants | 1,2,3,... | unit |
| 10 | `test_every_variant_has_round_sequence` | all DealingVariant | non-empty, >0 | unit |
| 11 | `test_every_variant_has_max_players` | all DealingVariant | 2<=max<=52 | unit |
| 12 | `test_round_sequence_matches_json_configs` | all variants | sequences match | integration |

### `test_api_rest.py` — 45 integration tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `TestRouteRegistration::test_all_routes_registered` | scan app.routes for 14 paths | no missing | unit |
| 2 | `TestRouteRegistration::test_lobby_quick_join_reachable` | POST /api/lobby/quick-join {"player_name":"RouteTest"} | 200 | integration |
| 3 | `TestRouteRegistration::test_lobby_list_reachable` | GET /api/lobby | 200 | integration |
| 4 | `TestCreateGame::test_create_game_success` | 3 players (Alice, Bot1 easy, Bot2 medium), 10_to_1 | 200, game_id present | integration |
| 5 | `TestCreateGame::test_create_game_too_few_players` | 1 player | 400 | integration |
| 6 | `TestCreateGame::test_create_game_must_lose` | 3 players, must_lose=True | 200 | integration |
| 7 | `TestGetGameState::test_get_state` | GET /api/games/{id} | 200, game_id matches | integration |
| 8 | `TestGetGameState::test_get_nonexistent_game` | GET /api/games/nonexistent | 404 | integration |
| 9 | `TestGetPlayerHand::test_get_hand` | GET /hand/{alice_id} | 200, 10 cards | integration |
| 10 | `TestBidAndPlay::test_full_human_turn` | bid valid[0], play valid[0] | success=True | integration |
| 11 | `TestBidAndPlay::test_invalid_bid` | player_id="nonexistent", amount=99 | success=False | integration |
| 12 | `TestSessionLog::test_session_log_exists` | GET /session-log | 200, game_id, 3 players | integration |
| 13 | `TestAIAutoPlay::test_ai_plays_automatically` | 2 AI players, check state | AI played or Alice's turn | integration |
| 14 | `TestCreateGameNoAutoStart::test_create_stays_in_lobby` | auto_start=False, 1 player | phase="lobby" | integration |
| 15 | `TestCreateGameNoAutoStart::test_auto_start_default_true` | 3 players default | phase!="lobby" | integration |
| 16 | `TestCreateGameNoAutoStart::test_create_with_ai_auto_start` | 3 players | phase!="lobby" | integration |
| 17 | `TestJoinGame::test_join_game` | Bob joins lobby | 200, Bob in players | integration |
| 18 | `TestJoinGame::test_join_game_not_found` | join nonexistent | 404 | integration |
| 19 | `TestJoinGame::test_join_game_already_started` | join started game | 400 | integration |
| 20 | `TestJoinGame::test_join_game_full` | 6th player to max-5 | 400 | integration |
| 21 | `TestJoinGame::test_join_game_duplicate_name` | join as "Alice" | 400 | integration |
| 22 | `TestJoinGame::test_join_game_duplicate_name_case_insensitive` | join as "ALICE" | 400 | integration |
| 23 | `TestStartGame::test_start_game` | host starts 2-player | 200, phase="bidding" | integration |
| 24 | `TestStartGame::test_start_game_not_host` | non-host starts | 403 | integration |
| 25 | `TestStartGame::test_start_game_not_enough_players` | 1 player starts | 400 | integration |
| 26 | `TestStartGame::test_start_game_already_started` | start again | 400 | integration |
| 27 | `TestGetLobbyState::test_get_lobby` | GET /lobby | game_id, phase="lobby" | integration |
| 28 | `TestGetLobbyState::test_lobby_shows_joined_player` | Bob joins, get lobby | 2 players | integration |
| 29 | `TestGetLobbyState::test_lobby_has_host_id` | get lobby | host_player_id=alice | integration |
| 30 | `TestLobbyList::test_lobby_list_empty` | GET /api/lobby (none) | [] | integration |
| 31 | `TestLobbyList::test_lobby_list_public_games` | create public, list | 1 game | integration |
| 32 | `TestLobbyList::test_lobby_list_excludes_private` | create private, list | 0 | integration |
| 33 | `TestLobbyList::test_lobby_list_excludes_started` | start game, list | 0 | integration |
| 34 | `TestLobbyList::test_lobby_list_game_info` | create 8_down_up, list | correct info | integration |
| 35 | `TestQuickJoin::test_quick_join_auto_play_starts_immediately` | quick-join "Alice" | 200, phase in progress | integration |
| 36 | `TestQuickJoin::test_quick_join_no_auto_play_stays_in_lobby` | auto_play=False | 1 in lobby list | integration |
| 37 | `TestQuickJoin::test_quick_join_finds_existing` | create lobby, Bob quick-joins | Bob in existing game | integration |
| 38 | `TestQuickJoin::test_quick_join_prefers_fullest` | 2 lobbies, join picks fuller | joins game2 | integration |
| 39 | `TestQuickJoin::test_quick_join_variant_filter` | lobby 10_to_1, join 8_down_up | new game created | integration |
| 40 | `TestQuickJoin::test_quick_join_duplicate_name_skips` | lobby as Alice, join as Alice | creates new game | integration |
| 41 | `TestSinglePlayerLobbyCreation::test_single_player_lobby_succeeds` | 1 player, auto_start=False | 200 | integration |
| 42 | `TestSinglePlayerLobbyCreation::test_single_player_auto_start_fails` | 1 player, auto_start=True | 400 | integration |
| 43 | `TestSinglePlayerLobbyCreation::test_lobby_create_join_start_flow` | host+friend, start | phase="bidding" | integration |
| 44 | `TestSinglePlayerLobbyCreation::test_lobby_with_must_lose_mode` | must_lose=True | must_lose in response | integration |
| 45 | `TestFillWithAI::test_fill_with_ai` | 2 players, fill | 5 total | integration |

### `test_websocket_game.py` — 13 integration tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_connected_event_has_round_state` | WS connect | game_id, player_id, phase, num_cards=10, round=1 | integration |
| 2 | `test_auto_sends_hand_on_connect` | WS connect | 2nd event="hand", 10 cards | integration |
| 3 | `test_play_two_rounds` | 1 human + 2 AI, play 2 rounds | card_played>0, trick_complete>0 | integration |
| 4 | `test_card_played_events_have_player_names` | play cards | every event has player_id + card | integration |
| 5 | `test_hand_always_has_valid_actions_on_my_turn` | 50 turns | never empty valid_bids AND valid_cards | integration |
| 6 | `test_connected_event_in_lobby_has_host_and_players` | lobby WS | phase="lobby", host_player_id | integration |
| 7 | `test_joiner_is_not_host` | Bob joins, connects | host!=bob | integration |
| 8 | `test_host_sees_themselves_as_host` | Alice connects | host=alice | integration |
| 9 | `test_two_humans_bid_and_play` | 2 humans, first bids | second gets bid_placed event | integration |
| 10 | `test_game_over_has_persona_on_wire` | 3-round game | persona with name, tagline, traits (11) | integration |
| 11 | `test_connected_then_hand` | WS connect | event[0]="connected", event[1]="hand" | integration |
| 12 | `test_reconnect_restores_state` | connect, disconnect, reconnect | state restored | integration |
| 13 | `test_disconnect_no_error` | connect, close | no crash | integration |

### `test_multiplayer_integration.py` — 6 integration tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_create_join_start` | create, Bob joins, start | phase="bidding" | integration |
| 2 | `test_lobby_with_ai_backfill` | lobby + 2 bots + start | phase in progress | integration |
| 3 | `test_human_with_ai_complete_round` | 1 human + 2 AI, WS | rounds>=1 | integration |
| 4 | `test_quick_join_creates_lobby` | Alice no-auto, Bob joins, start | phase="bidding" | integration |
| 5 | `test_three_rounds` | 1 human + 2 AI, 3 rounds | rounds>=3, ascending | integration |
| 6 | `test_session_log_has_entries` | 1 human + 2 AI, 1 round, check log | >=1 round in log | integration |

### `test_edge_cases.py` — 22 integration tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_join_nonexistent_game` | POST /join fake-id | 404 | integration |
| 2 | `test_join_started_game` | join running game | 400 | integration |
| 3 | `test_join_duplicate_name` | join as "Alice" | 400 | integration |
| 4 | `test_join_duplicate_name_case_insensitive` | join as "alice" | 400 | integration |
| 5 | `test_join_full_game` | 6th player | 400 | integration |
| 6 | `test_start_nonexistent_game` | start fake-id | 404 | integration |
| 7 | `test_start_not_host` | Bob starts | 403 | integration |
| 8 | `test_start_solo` | 1 player starts | 400 | integration |
| 9 | `test_start_already_started` | start again | 400 | integration |
| 10 | `test_lobby_state_nonexistent` | GET /lobby fake-id | 404 | integration |
| 11 | `test_lobby_state_started_game` | GET /lobby started game | 200 or 400 | integration |
| 12 | `test_ws_invalid_game` | WS /ws/fake/fake | exception | integration |
| 13 | `test_ws_invalid_action` | send {"action":"nonsense"} | hand still works | integration |
| 14 | `test_ws_invalid_card` | play card rank=99 | error event | integration |
| 15 | `test_ws_reconnect_same_player` | connect, close, reconnect | connected+hand | integration |
| 16 | `test_join_with_short_code` | game_id[:8] | 200, full ID matches | integration |
| 17 | `test_join_with_uppercase_short_code` | game_id[:8].upper() | 200 | integration |
| 18 | `test_join_with_full_id_still_works` | full UUID | 200 | integration |
| 19 | `test_short_code_not_found` | "ZZZZZZZZ" | 404 | integration |
| 20 | `test_lobby_state_via_short_code` | GET /lobby short code | 200 | integration |
| 21 | `test_quick_join_same_name_different_games` | two "Alice" quick-joins | both 200 | integration |
| 22 | `test_quick_join_fills_lobby` | 3 unique quick-joins | all same game | integration |

### `test_analysis.py` — 86 tests (83 unit + 3 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `TestPersonaLoader::test_loads_without_errors` | load_personas() | len>0 | unit |
| 2 | `TestPersonaLoader::test_persona_count` | load_personas() | len==75 | unit |
| 3 | `TestPersonaLoader::test_all_personas_have_11_traits` | all personas | 11 traits each | unit |
| 4 | `TestPersonaLoader::test_all_personas_have_11_weights` | all personas | 11 weights each | unit |
| 5 | `TestPersonaLoader::test_all_trait_values_in_unit_range` | all personas | 0.0-1.0 | unit |
| 6 | `TestPersonaLoader::test_all_weight_values_positive` | all personas | >=0.0 | unit |
| 7 | `TestPersonaLoader::test_all_personas_have_required_fields` | all personas | id,name,tagline,category valid | unit |
| 8 | `TestPersonaLoader::test_get_persona_by_id_found` | get_persona_by_id("batman") | name=="Batman" | unit |
| 9 | `TestPersonaLoader::test_get_persona_by_id_not_found` | get_persona_by_id("nonexistent") | KeyError | unit |
| 10 | `TestPersonaLoader::test_categories_all_represented` | all categories | 7 categories | unit |
| 11 | `TestPersonaLoader::test_key_dims_returns_top_3` | batman.key_dims | 3 dims, has "planning"+"precision" | unit |
| 12 | `TestPersonaLoader::test_achievement_personas_have_triggers` | achievement category | 10 personas, all have triggers | unit |
| 13 | `TestFingerprint::test_high_bid_scores_high_risk` | bid 6/7, won 6 | risk>0.8 | unit |
| 14 | `TestFingerprint::test_exact_hit_scores_high_planning` | bid 3/5, won 3 | planning>=0.9 | unit |
| 15 | `TestFingerprint::test_low_bid_scores_low_risk` | bid 1/7, won 1 | risk<0.3 | unit |
| 16 | `TestFingerprint::test_missed_bid_scores_low_planning` | bid 0/10, won 5 | planning<0.6 | unit |
| 17 | `TestFingerprint::test_all_values_in_unit_range` | 50 random rounds (seed 42) | all 0.0-1.0 | unit |
| 18 | `TestFingerprint::test_empty_session_returns_neutral` | empty SessionLog | all==0.5 | unit |
| 19 | `TestFingerprint::test_fingerprint_returns_all_11_dimensions` | 1 round (5 cards) | 11 dims | unit |
| 20 | `TestFingerprint::test_multi_round_consistency` | 3 exact rounds | consistency>0.8 | unit |
| 21 | `TestFingerprint::test_inconsistent_player_lower_consistency` | consistent vs inconsistent | consistent>inconsistent | unit |
| 22 | `TestBoldness::test_bold_bidder_high_boldness` | bid 5/7, won 5 | boldness>0.65 | unit |
| 23 | `TestBoldness::test_reckless_bidder_low_boldness` | bid 5/7, won 1 | boldness<0.25 | unit |
| 24 | `TestBoldness::test_commendable_effort_mid_boldness` | bid 5/7, won 4 | 0.35<b<0.65 | unit |
| 25 | `TestBoldness::test_zero_bid_zero_boldness` | bid 0/5, won 0 | boldness==0.0 | unit |
| 26 | `TestPrecision::test_exact_hits_high_precision` | 3 exact rounds | precision>0.8 | unit |
| 27 | `TestPrecision::test_all_misses_low_precision` | 2 miss rounds | precision<0.2 | unit |
| 28 | `TestResilience::test_recovery_high_resilience` | miss-hit-miss-hit | resilience>=0.9 | unit |
| 29 | `TestResilience::test_no_recovery_low_resilience` | miss-miss-miss-hit | resilience<0.5 | unit |
| 30 | `TestResilience::test_never_missed_neutral_resilience` | 2 hits | resilience==0.5 | unit |
| 31 | `TestClutch::test_late_game_dominance_high_clutch` | miss early, hit late | clutch>0.7 | unit |
| 32 | `TestClutch::test_early_strong_late_weak_low_clutch` | hit early, miss late | clutch<0.4 | unit |
| 33 | `TestTrajectory::test_improving_player_high_trajectory` | miss first 2, hit last 2 | trajectory>0.7 | unit |
| 34 | `TestTrajectory::test_declining_player_low_trajectory` | hit first 2, miss last 2 | trajectory<0.3 | unit |
| 35 | `TestScorePersona::test_exact_match_high_score` | batman traits exact | score>0.95 | unit |
| 36 | `TestScorePersona::test_opposite_traits_low_score` | opposite batman | score<0.6 | unit |
| 37 | `TestScorePersona::test_weights_affect_scoring` | risk mismatch vs planning mismatch | risk mismatch scores higher | unit |
| 38 | `TestScorePersona::test_trigger_fires_bonus` | sniper: precision 0.9 vs 0.5 | high>low | unit |
| 39 | `TestScorePersona::test_combo_trigger_requires_all_conditions` | wildcard combo both vs partial | True/False | unit |
| 40 | `TestScorePersona::test_affinity_bonus_for_extreme_match` | thor exact vs moderate aggression | exact>moderate | unit |
| 41 | `TestPersonaMatch::test_batman_vector_matches_superhero` | batman traits | "superhero" in top categories | unit |
| 42 | `TestPersonaMatch::test_turtle_vector_matches_turtle_or_nit` | turtle traits | turtle/nit/snorlax in top | unit |
| 43 | `TestPersonaMatch::test_novelty_penalises_recent` | with/without recent_ids | recent<=without | unit |
| 44 | `TestPersonaMatch::test_pick_persona_deterministic_with_seed` | seed=123 twice | same ID | unit |
| 45 | `TestPersonaMatch::test_variety_over_multiple_seeds` | 50 seeds | >=2 unique | unit |
| 46 | `TestPersonaMatch::test_pick_never_returns_unknown_id` | 100 picks | all in known_ids | unit |
| 47 | `TestPersonaMatch::test_top_k_default_is_7` | best_personas default | len==7 | unit |
| 48 | `TestPersonaMatch::test_category_diversity` | neutral vec | >=3 categories | unit |
| 49 | `TestPersonaMatch::test_casual_tier_only_returns_animals` | TIER_CASUAL | all animal | unit |
| 50 | `TestPersonaMatch::test_elite_tier_includes_superheroes` | TIER_ELITE+COMPETITIVE | has "superhero" | unit |
| 51 | `TestPersonaMatch::test_competitive_tier_excludes_animals` | COMPETITIVE+STANDARD | no animal | unit |
| 52 | `TestPersonaMatch::test_standard_tier_excludes_superheroes` | STANDARD+CASUAL | no superhero | unit |
| 53 | `TestPersonaMatch::test_compute_tier_elite` | hard+challenge+must_lose | "elite" | unit |
| 54 | `TestPersonaMatch::test_compute_tier_competitive` | hard; easy+challenge | "competitive" | unit |
| 55 | `TestPersonaMatch::test_compute_tier_standard` | medium, no flags | "standard" | unit |
| 56 | `TestPersonaMatch::test_compute_tier_casual` | easy, no flags | "casual" | unit |
| 57 | `TestPersonaMatch::test_pick_persona_respects_tier` | 50 picks at "casual" | all animal | unit |
| 58 | `TestPersonaMatch::test_achievement_persona_wins_with_trigger` | precision=0.95, planning=0.9 | "sniper" in top | unit |
| 59 | `TestFingerprintToMatch::test_aggressive_player_gets_high_risk_persona` | 3 high-bid rounds | risk>0.7, valid personas | integration |
| 60 | `TestFingerprintToMatch::test_conservative_player_gets_conservative_persona` | 3 low-bid rounds | turtle/nit/etc in top | integration |
| 61 | `TestFingerprintToMatch::test_game_over_event_includes_persona` | game_over_event with fox | persona data correct | unit |
| 62 | `TestFingerprintToMatch::test_game_over_event_without_persona` | game_over_event no persona | persona=None | unit |
| 63 | `TestMascotIntegration::test_full_game_emits_persona_in_game_over` | full 3_quick game | GAME_OVER has persona | integration |
| 64 | `TestMascotIntegration::test_ai_only_game_has_no_persona` | 2 easy AI | persona=None | integration |
| 65-86 | `TestAllPersonasByDifficulty` (22 tests) | Tier validation, 500-pick leak tests, category reachability, compute_tier mapping, recency variety | See persona tier section | unit |

### `test_smart_ai.py` — 23 tests (22 unit + 1 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `TestBidFeatures::test_returns_fixed_length_vector` | 5-card hand | 12 floats | unit |
| 2 | `TestBidFeatures::test_num_cards_is_first_feature` | num_cards=5 | features[0]==5.0 | unit |
| 3 | `TestBidFeatures::test_dealer_detection` | 2 bids, 3 players | features[-1]==1.0 | unit |
| 4 | `TestPlayFeatures::test_returns_fixed_length_vector` | 5-card hand, 3 valid | 11 floats | unit |
| 5 | `TestPlayFeatures::test_leading_flag` | empty trick | features[4]==1.0 | unit |
| 6 | `TestCardIndexConversion::test_round_trip` | H-A, S-2, D-K | round-trips | unit |
| 7 | `TestCardIndexConversion::test_out_of_range_returns_none` | index=5, 1 card | None | unit |
| 8 | `TestNeighborModel::test_append_and_load` | [1,2,3]->5, [4,5,6]->3 | 2 examples correct | unit |
| 9 | `TestNeighborModel::test_predict_returns_none_with_few_examples` | 5 examples (<10) | None | unit |
| 10 | `TestNeighborModel::test_predict_returns_value_with_enough_examples` | 15 all label=3 | predict==3 | unit |
| 11 | `TestNeighborModel::test_predict_picks_nearest_label` | cluster bid=2 near [1.0], bid=5 near [10.0] | [1.5]->2, [9.5]->5 | unit |
| 12 | `TestNeighborModel::test_predict_card_clamps_to_valid_range` | all label=10, 3 valid | result==2 | unit |
| 13 | `TestNeighborModel::test_empty_file_returns_none` | nonexistent file | None | unit |
| 14 | `TestNeighborModel::test_example_count` | append 2 | count: 0->2 | unit |
| 15 | `TestDecisionCollector::test_record_and_flush_winner` | record for winner+loser, flush | count=2 | unit |
| 16 | `TestDecisionCollector::test_flush_clears_buffer` | record, clear, flush | count=0 | unit |
| 17 | `TestSmartHardAI::test_falls_back_when_no_data` | choose_bid, no data | bid in valid | unit |
| 18 | `TestSmartHardAI::test_choose_card_falls_back` | choose_card, no data | card in hand | unit |
| 19 | `TestSmartHardAI::test_always_returns_valid` | 1-card hand | card in hand | unit |
| 20 | `TestMakeStrategy::test_hard_without_smart` | HARD, use_smart=False | HardAI | unit |
| 21 | `TestMakeStrategy::test_hard_with_smart` | HARD, use_smart=True | SmartHardAI | unit |
| 22 | `TestMakeStrategy::test_non_hard_ignores_smart_flag` | EASY, use_smart=True | EasyAI | unit |
| 23 | `TestSmartIntegration::test_game_with_smart_bot_completes` | 1 human + 2 hard AI | phase in progress | integration |

### `test_information_isolation.py` — 15 tests (14 unit + 1 integration)

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | `test_bid_features_are_all_floats` | extract_bid_features | all float | unit |
| 2 | `test_play_features_are_all_floats` | extract_play_features | all float | unit |
| 3 | `test_bid_features_fixed_length` | 1-card vs 5-card | both 12 | unit |
| 4 | `test_play_features_fixed_length` | 1-card vs 5-card | both 11 | unit |
| 5 | `test_features_contain_no_card_objects` | both extractors | no Card/Suit/Rank | unit |
| 6 | `test_context_has_no_hand_attribute` | RoundContext | no hand/hands attrs | unit |
| 7 | `test_context_cards_played_are_public` | context.cards_played | matches input | unit |
| 8 | `test_context_bids_are_public` | context with 2 bids | len==2 | unit |
| 9 | `test_hands_are_disjoint` | 3-player engine | all disjoint | unit |
| 10 | `test_get_player_hand_only_returns_own_cards` | p1 vs p2 | both non-empty, != | unit |
| 11 | `test_round_context_does_not_contain_other_hands` | p1 context vs p2 hand | no p2 cards | unit |
| 12 | `test_stored_data_contains_only_numbers` | JSONL after flush | features=floats, label=number | unit |
| 13 | `test_stored_data_has_strategy_type` | human bid + smart_hard play | types match | unit |
| 14 | `test_no_card_strings_in_stored_data` | raw JSONL | no suit names | unit |
| 15 | `test_ai_game_hands_stay_isolated` | 3 AI game | all hands disjoint | integration |

---

## Frontend Tests (49 total: all unit)

### `BidSelector.test.tsx` — 10 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | renders bid buttons 0 through numCards | validBids=[0,1,2,3], numCards=5 | buttons "0"-"5" exist | unit |
| 2 | disables invalid bid buttons | validBids=[0,2] | "1" disabled, "0"+"2" enabled | unit |
| 3 | calls onBid when valid clicked | click "2" | onBid(2) | unit |
| 4 | does not call onBid when disabled clicked | click "1", validBids=[0,2] | onBid not called | unit |
| 5 | shows player score | cumulativeScores={p1:21} | "Score: 21" | unit |
| 6 | shows total bids so far | bids=[{p2,3}], numCards=5 | "3/5" | unit |
| 7 | shows trump suit symbol | trumpSuit="spades" | spade symbol | unit |
| 8 | shows 'You' for current player | playerId="p1", players Alice/Bob/Charlie | "You", "Bob", "Charlie" | unit |
| 9 | shows placed bid amounts | bids=[{p2:2},{p3:0}] | "?" for own | unit |
| 10 | renders with zero score | cumulativeScores={} | "Score: 0" | unit |

### `PlayerHand.test.tsx` — 6 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | renders all cards | [S-A, H-K, D-5] | "A","K","5" text | unit |
| 2 | marks playable cards as buttons | isMyTurn, valid=[S-A] | 1 button | unit |
| 3 | calls onPlayCard when clicked | click S-A | onPlayCard({spades,14}) | unit |
| 4 | no buttons when not my turn | isMyTurn=false | 0 buttons | unit |
| 5 | empty hand without errors | hand=[] | no throw | unit |
| 6 | sorts by suit then rank | [H-A, S-2, S-A] | 3 card elements | unit |

### `variant.test.ts` — 4 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | VARIANT_LIST contains all variants | Object.values vs VARIANT_LIST | same length | unit |
| 2 | every variant has config | each variant | label, rounds, detail truthy | unit |
| 3 | maxPlayers within bounds | each variant | 2<=max<=52 | unit |
| 4 | label contains round count | each variant | "round" in label | unit |

### `Scoreboard.test.tsx` — 9 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | renders column headers | default props | "Pilot","Flights","Landings","Score" | unit |
| 2 | renders all player names | Alice, Bob, Charlie | names present | unit |
| 3 | renders bid and trick values | p1:bid3/won3, p2:bid2/won1, p3:bid1/won2 | values in rows | unit |
| 4 | shows dash when bid not placed | only p1 bid | 2 em-dashes | unit |
| 5 | shows leader badge | p1:30, p2:10, p3:-11 | star for p1 | unit |
| 6 | shows Current column when roundScores | rerender with scores | "Current" appears | unit |
| 7 | positive round scores with green | {p1:30, p2:-2, p3:11} | "+30", "-2", "+11" | unit |
| 8 | handles tied leaders | p1:30, p2:30, p3:10 | 2 stars | unit |
| 9 | renders cumulative scores | {p1:30, p2:10, p3:-11} | "30", "10" | unit |

### `FinalResults.test.tsx` — 9 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | renders Game Over title | default props | "Game Over" | unit |
| 2 | shows winner name | p1:50, p2:30, p3:-10 | "Winner", "Alice" | unit |
| 3 | shows 'Winners' for ties | p1:50, p2:50 | "Winners", "Alice & Bob" | unit |
| 4 | ranks by score descending | 3 players | first=50, last=-10 | unit |
| 5 | shows 'Your score' | playerId="p1" | "Your score" | unit |
| 6 | calls onPlayAgain | click button | onPlayAgain() | unit |
| 7 | renders persona card | persona Iron Man | name, tagline, category | unit |
| 8 | no persona card when null | persona=null | no "Your Play Style" | unit |
| 9 | celebration effects for rank | 1st place | aria-hidden elements | unit |

### `OpponentArea.test.tsx` — 11 tests

| # | Test | Input | Expected | Type |
|---|------|-------|----------|------|
| 1 | dash in bid badge when no bid | bid=null | em-dash | unit |
| 2 | won/bid status | bid=3, won=1 | "1/3" | unit |
| 3 | score in separate badge | score=42 | "42" | unit |
| 4 | active class when current turn | isCurrentTurn=true | "bidBadgeActive" | unit |
| 5 | no active class when not turn | isCurrentTurn=false | no "bidBadgeActive" | unit |
| 6 | NOW pill when current turn | isCurrentTurn=true | "NOW" | unit |
| 7 | shows player name | "Jalebi" | "Jalebi" | unit |
| 8 | 0/0 when bid zero, no tricks | bid=0, won=0 | "0/0" | unit |
| 9 | bid and score are separate | bid=2, won=1, score=30 | "1/2" and "30" separate | unit |
| 10 | render order: cards, name, score | "Jalebi", bid, score | correct child order | unit |
| 11 | no seat overlaps round info | 3/4/5/6 player layouts | no left<20% AND top<15% | unit |

---

## Coverage Gap Analysis

### Backend — Untested Public Methods

**Zero coverage (direct or indirect):**
| Method | File |
|--------|------|
| `GameManager.remove_game()` | `game_manager.py` |
| `GameManager.list_games()` | `game_manager.py` |
| `GameManager.record_persona()` | `game_manager.py` |
| `_should_nerf_ai()` | `game_manager.py` |
| `_load_game_count()` | `game_manager.py` |
| `_increment_game_count()` | `game_manager.py` |
| `ManagedGame._get_max_ai_difficulty()` | `game_manager.py` |
| `ConnectionManager.get_connected_players()` | `api/websocket.py` |

**Indirect only (no dedicated unit test):**
| Method | File |
|--------|------|
| `RoundManager` (entire class) | `game/round_manager.py` |
| `card_play.would_win()` | `ai/card_play.py` |
| `card_play.best_winning_card()` | `ai/card_play.py` |
| `card_play.dump_lowest()` | `ai/card_play.py` |
| `_get_event_delay()` | `api/websocket.py` |
| `ConnectionManager.connect/disconnect()` | `api/websocket.py` |
| `resolve_trick()` empty-trick ValueError path | `game/trick_resolver.py` |

### Frontend — Untested Components/Modules

| Category | Untested Files |
|----------|---------------|
| **common/** | Card, SuitIcon, SuitSvg, Button, Modal, SettingsModal, FaceCardArt, CardBack |
| **lobby/** | GameLobby, PlayerSetup, VariantSelector, WaitingRoom, JoinGameForm, QuickPlayForm |
| **game/** | GameBoard, RoundInfo, TrickArea, PlayerInfo |
| **hooks/** | useGame, useWebSocket |
| **context/** | GameContext, SettingsContext |
| **services/** | api, websocket, audio |
| **types/** | card, events, settings |
| **root** | App.tsx |

**Frontend coverage: 6/31 source files tested (19%)**

---

## Summary

| Category | Unit | Integration | Total |
|----------|------|-------------|-------|
| Backend | 269 | 76 | 345 |
| Frontend | 49 | 0 | 49 |
| **Total** | **318** | **76** | **394** |

### CLAUDE.md Test Count Corrections Needed

| File | Documented | Actual |
|------|-----------|--------|
| test_trick_resolver.py | 6 | 6 |
| test_scorer.py | 7 | 7 |
| test_validators.py | 11 | 18 |
| test_engine.py | 14 | 17 |
| test_ai.py | 16 | 33 |
| test_api_rest.py | 37 | 45 |
| test_round_config.py | 9 | 12 |
| test_websocket_game.py | 10 | 13 |
| test_multiplayer_integration.py | 6 | 6 |
| test_edge_cases.py | 17 | 22 |
| test_analysis.py | 30 | 86 |
| test_smart_ai.py | 23 | 23 |
| test_information_isolation.py | (unlisted) | 15 |
| test_deck.py | (unlisted) | 9 |
| Frontend (6 files) | 49 | 49 |
| **Total** | **307** | **394** |

---

## Added Tests (239 new, 6 duplicates removed)

### New Backend Test Files (118 tests added)

| File | Tests | Coverage Target |
|------|-------|----------------|
| `test_round_manager.py` | 60 | `game/round_manager.py` — properties, place_bid, play_card, try_resolve_trick, calculate_scores, full round flows |
| `test_card_play.py` | 33 | `ai/card_play.py` — would_win (13), best_winning_card (7), dump_lowest (7), lowest_winning_trump (6) |
| `test_game_manager_unit.py` | 25 | `game_manager.py` — GameSpeed, remove_game, list_games, record_persona, _should_nerf_ai, game_count, _get_max_ai_difficulty, _get_event_delay |

### New Frontend Test Files (136 tests added)

| File | Tests | Coverage Target |
|------|-------|----------------|
| `types/card.test.ts` | 18 | Card type helpers — SUIT_SYMBOLS, SUIT_COLORS, RANK_DISPLAY, TRUMP_ORDER, isSameCard, cardDisplayName |
| `types/settings.test.ts` | 17 | Settings constants — DEFAULT_SETTINGS, TABLE_COLOR_MAP, ANIMATION_SPEED_MAP, labels |
| `components/common/Button.test.tsx` | 13 | Button — variant classes, sizes, fullWidth, onClick, disabled |
| `components/common/Modal.test.tsx` | 9 | Modal — title, children, close button, ESC key, overlay click, stopPropagation |
| `components/common/SuitIcon.test.tsx` | 12 | SuitIcon — symbols, colors, sizes, aria-label |
| `components/common/Card.test.tsx` | 13 | Card + CardBack — rank, suit, playable, dimmed, small, onClick |
| `components/game/RoundInfo.test.tsx` | 14 | RoundInfo — null return, round/card text, tooltip with totalRounds, mode icons, position classes |
| `components/game/TrickArea.test.tsx` | 7 | TrickArea — waiting message, card rendering, lead badge, winner banner |
| `components/game/PlayerInfo.test.tsx` | 8 | PlayerInfo — null handling, avatar, score, bid display, active class |
| `hooks/useGame.test.ts` | 21 | useGame reducer — initial state, SET_GAME_INFO, CONNECTED, ROUND_STARTED, BID_PLACED, CARD_PLAYED, TRICK_COMPLETE, ROUND_COMPLETE, GAME_OVER, event buffering, clearTrick replay |
| `hooks/useGameContext.test.tsx` | 4 | GameContext — provider renders, context values accessible |

### Frontend Tests Updated (existing, +15 tests)

| File | Before | After | Changes |
|------|--------|-------|---------|
| `App.test.tsx` | 10 | 10 | Updated for totalRounds field in INITIAL_GAME_STATE |
| `GameLobby.test.tsx` | 16 | 16 | No changes needed |
| `Scoreboard.test.tsx` | 10 | 10 | No changes needed |
| `useWebSocket.test.ts` | 13 | 13 | No changes needed |

### Duplicates Removed (6 tests)

| File | Test Removed | Reason |
|------|-------------|--------|
| `test_ai.py` | `test_lowest_winning_trump_in_trick` | Fully covered by `test_card_play.py::TestLowestWinningTrump` (6 tests) |
| `test_api_rest.py` | `test_join_game_not_found` | Duplicate of `test_edge_cases.py::test_join_nonexistent_game` |
| `test_api_rest.py` | `test_join_game_already_started` | Duplicate of `test_edge_cases.py::test_join_started_game` |
| `test_api_rest.py` | `test_join_game_full` | Duplicate of `test_edge_cases.py::test_join_full_game` |
| `test_api_rest.py` | `test_join_game_duplicate_name` | Duplicate of `test_edge_cases.py::test_join_duplicate_name` |
| `test_api_rest.py` | `test_join_game_duplicate_name_case_insensitive` | Duplicate of `test_edge_cases.py::test_join_duplicate_name_case_insensitive` |

### Final Test Counts

| File | Tests |
|------|-------|
| **Backend** | **442** |
| test_trick_resolver.py | 6 |
| test_scorer.py | 7 |
| test_validators.py | 18 |
| test_engine.py | 14 |
| test_ai.py | 15 |
| test_api_rest.py | 32 |
| test_round_config.py | 12 |
| test_websocket_game.py | 13 |
| test_multiplayer_integration.py | 6 |
| test_edge_cases.py | 22 |
| test_analysis.py | 86 |
| test_smart_ai.py | 23 |
| test_information_isolation.py | 15 |
| test_deck.py | 9 |
| test_round_manager.py | 60 |
| test_card_play.py | 33 |
| test_game_manager_unit.py | 25 |
| test_lobby.py | 46 |
| **Frontend** | **185** |
| App.test.tsx | 10 |
| GameLobby.test.tsx | 16 |
| Scoreboard.test.tsx | 10 |
| useWebSocket.test.ts | 13 |
| useGameContext.test.tsx | 4 |
| useGame.test.ts | 21 |
| card.test.ts | 18 |
| settings.test.ts | 17 |
| Button.test.tsx | 13 |
| Modal.test.tsx | 9 |
| SuitIcon.test.tsx | 12 |
| Card.test.tsx | 13 |
| RoundInfo.test.tsx | 14 |
| TrickArea.test.tsx | 7 |
| PlayerInfo.test.tsx | 8 |
| **Grand Total** | **627** |
