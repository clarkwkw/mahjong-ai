import random
import Tile

class Game:
	def __init__(self, players):
		self.__players = players
		self.__deck = Tile.get_tiles(shuffle = True)
		for player in players:
			hand = self.__deck[0:13]
			self.__deck = self.__deck[13:len(self.__deck)]
			player.reset_hand(hand)

	def start_game(self):
		cur_player_id = 0
		new_tile = None
		is_ponged, is_chowed, is_vict = False, False, False
		while len(self.__deck) > 0:
			cur_player = self.__players[cur_player_id]
			neighbors = self.__get_neighbor_players(cur_player_id)

			# If the player formed Kong, let him/her draw again
			while True:
				if not is_ponged and not is_chowed:
					new_tile = self.__deck.pop(0)
				else:
					new_tile = None
				
				dispose_tile, score = cur_player.new_turn(new_tile, neighbors)
				
				if score is not None:
					return cur_player, self.__get_neighbor_players(cur_player_id, degenerated = False), score

				if dispose_tile is not None:
					break

			is_ponged, is_chowed = False, False

			# Check whether any of the other players can win by stealing
			check_player_id = (cur_player_id + 1)%4
			while check_player_id != cur_player_id:
				check_player = self.__players[check_player_id]
				neighbors = self.__get_neighbor_players(check_player_id)
				is_able, is_wants_to, score = check_player.check_win(dispose_tile, "steal", neighbors)
				
				if is_wants_to is not None and is_wants_to:
					return check_player, [cur_player], score
					
				check_player_id = (check_player_id + 1)%4

			# Check whether any of the other players "is able to" and "wants to" Pong/ Kong
			check_player_id = (cur_player_id + 1)%4
			tile_used = False
			while check_player_id != cur_player_id:
				is_able_pong, is_able_kong = False, False

				check_player = self.__players[check_player_id]

				neighbors = self.__get_neighbor_players(check_player_id)
				is_able_kong, is_wants_kong, location = check_player.check_kong(dispose_tile, include_non_fix_hand = True, neighbors = neighbors)
				if is_able_kong and is_wants_kong:

					check_player.kong(dispose_tile, location = location, source = "steal")
					tile_used = True
					cur_player_id = check_player_id
				else:

					is_able_pong, is_wants_pong = check_player.check_pong(dispose_tile, neighbors)
					if is_able_pong and is_wants_pong:
						check_player.pong(dispose_tile)
						tile_used = True
						cur_player_id = check_player_id
						is_ponged = True

				if is_able_pong or is_able_kong:
					break

				check_player_id = (check_player_id + 1)%4

			# If a player 'steals' the tile to form Pong/ Kong meld, let him/her take the next round
			if tile_used:
				continue

			# If no one wants to Pong/Kong, check whether the next player wants to Chow
			next_player = self.__players[(cur_player_id+1)%4]
			neighbors = self.__get_neighbor_players((cur_player_id + 1)%4)
			is_able, is_wants_to, which = next_player.check_chow(dispose_tile, neighbors)
			if is_able and is_wants_to:
				next_player.chow(dispose_tile, which)
				tile_used = True
				is_chowed = True

			# No one wants to Pong/Kong/Chow, mark the tile as unstolen
			if not tile_used:
				cur_player.mark_last_discard_unstolen()

			cur_player_id = (cur_player_id+1)%4

		return None, None, None

	def __get_neighbor_players(self, player_id, degenerated = True):
		tmp_player_id = (player_id + 1)%4
		neighbors = []

		while tmp_player_id != player_id:
			player = self.__players[tmp_player_id]
			if degenerated:
				player = player.degenerate(mask_secret_meld = True)
			neighbors.append(player)
			tmp_player_id = (tmp_player_id + 1)%4

		return tuple(neighbors)