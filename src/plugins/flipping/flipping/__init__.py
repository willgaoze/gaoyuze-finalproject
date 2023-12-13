"""
This is where the implementation of the plugin code goes.
The Flipping-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('Flipping')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Flip_Highlight_Counting_3in1(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        META = self.META
        logger.debug('path: {0}'.format(core.get_path(active_node)))
        logger.info('name: {0}'.format(core.get_attribute(active_node, 'name')))
        logger.warn('pos : {0}'.format(core.get_registry(active_node, 'position')))
        logger.error('guid: {0}'.format(core.get_guid(active_node)))

        # In this game, the beginning condition has four basic pieces on tiles
        # By default, I set the currentMove in newname point to a random white piece, the currentPlayer
        # point to PlayerWhite. In this way, the PlayerBlack plays first.
        Game = core.get_parent(core.get_parent(active_node))
        activeNodes = core.load_sub_tree(Game)
        gameStateIndex = 0
        white_count = 0
        black_count = 0
        placed_tile = []

        old_player_path = core.get_pointer_path(Game, 'currentPlayer')
        nodesDict = dict()
        for node in activeNodes:
            nodesDict[core.get_path(node)] = node
        old_player_name = core.get_attribute(nodesDict[old_player_path], 'name')

        old_move_path = core.get_pointer_path(Game, 'currentMove')
        old_move_color = core.get_attribute(nodesDict[old_move_path], 'color')

        # set color of the piece which the player placed on this tile
        if old_move_color == 'white':
            next_color = 'black'
        else:
            next_color = 'white'

        while gameStateIndex < len(activeNodes):
            gameStateNode = activeNodes[gameStateIndex]
            if core.is_instance_of(gameStateNode, META['Piece']):
                row = core.get_attribute(core.get_parent(gameStateNode), 'row')
                column = core.get_attribute(core.get_parent(gameStateNode), 'column')
                color = core.get_attribute(gameStateNode, 'color')
                this_tile = (row, column, color)
                placed_tile.append(this_tile)
            gameStateIndex += 1

        # Make a board and store placed pieces on it
        board = []
        for i in range(8):
            row = []
            for j in range(8):
                row.append(None)
            board.append(row)
        for i in placed_tile:
            row = i[0]
            column = i[1]
            color = i[2]
            board[row][column] = color

        # run can_be_placed check on this tile
        tile = (core.get_attribute(active_node, 'row'), core.get_attribute(active_node, 'column'))
        truth_value = is_valid_move(board, tile, next_color)

        # if this tile can be placed
        if truth_value == True:
            copied_node = core.copy_node(core.get_parent(core.get_parent(active_node)),
                                         core.get_parent(core.get_parent(core.get_parent(active_node))))
            core.set_attribute(core.get_parent(core.get_parent(active_node)), 'name',
                               core.get_attribute(core.get_parent(core.get_parent(active_node)), 'name') + "_1")
            # Pointer player point to the player who placed piece in this tile
            for node in activeNodes:
                if core.is_instance_of(node, 'Player'):
                    if core.get_attribute(node, 'name') != old_player_name:
                        core.set_pointer(Game, 'currentPlayer', node)
                        break
            # Flip pieces
            new_board = flip_pieces(board, tile, next_color)
            flipped_tiles = find_changed_positions(board, new_board, tile)
            for i in flipped_tiles:
                row = i[0]
                column = i[1]
                gameStateIndex2 = 0
                while gameStateIndex2 < len(activeNodes):
                    gameStateNode = activeNodes[gameStateIndex2]
                    if core.is_instance_of(gameStateNode, META['Piece']):
                        tile_has_piece = core.get_parent(gameStateNode)
                        tile_row = core.get_attribute(tile_has_piece, 'row')
                        tile_column = core.get_attribute(tile_has_piece, 'column')
                        if (tile_row == row and tile_column == column):
                            core.set_attribute(gameStateNode, 'color', new_board[row][column])
                    gameStateIndex2 += 1
            # Place piece on current tile
            gameStateIndex3 = 0
            while gameStateIndex3 < len(activeNodes):
                gameStateNode = activeNodes[gameStateIndex3]
                if core.is_instance_of(gameStateNode, META['Tile']):
                    if (core.get_attribute(gameStateNode, 'row') == tile[0] and core.get_attribute(gameStateNode,
                                                                                                   'column') == tile[
                        1]):
                        placed_piece = core.create_child(gameStateNode, META['Piece'])
                        core.set_attribute(placed_piece, 'color', next_color)
                gameStateIndex3 += 1

                # pointer currentMove point to the piece on current tile
            activeNodes2 = core.load_sub_tree(Game)
            for node in activeNodes2:
                if core.is_instance_of(node, 'Piece'):
                    tile_nodes = core.get_parent(node)
                    tile_r = core.get_attribute(tile_nodes, 'row')
                    tile_c = core.get_attribute(tile_nodes, 'column')
                    if (tile_r == core.get_attribute(active_node, 'row')) and (
                            tile_c == core.get_attribute(active_node, 'column')):
                        core.set_pointer(Game, 'currentMove', node)
                        break

        # print the current player, board, can_be_placed on this tile.
        logger.info('can be placed: {0}'.format(truth_value))

        self.util.save(self.root_node, self.commit_hash, self.branch_name)

        # Highlight valid tiles for the next move
        next_available = []
        row = 0
        column = 0
        for row in range(8):
            for column in range(8):
                if is_valid_move(board, (row, column), next_color) == True:
                    next_available.append((row, column))

        # Counting pieces
        row = 0
        column = 0
        white_count = 0
        black_count = 0
        for row in range(8):
            for column in range(8):
                if board[row][column] == "white":
                    white_count += 1
                if board[row][column] == "black":
                    black_count += 1

        # Flipping is already done on above codes


def is_valid_move(board, tile, color):
    # Check if the tile is already occupied
    if board[tile[0]][tile[1]] is not None:
        return False
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1), (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    opposite_color = 'white' if color == 'black' else 'black'
    # Check all directions from the tile
    for direction in directions:
        tiles_to_flip = []
        for i in range(1, 8):
            x, y = tile[0] + direction[0] * i, tile[1] + direction[1] * i
            if 0 <= x < 8 and 0 <= y < 8:  # Stay within board limits
                current_tile = board[x][y]
                if current_tile == opposite_color:
                    tiles_to_flip.append((x, y))
                elif current_tile == color and tiles_to_flip:
                    return True  # Valid move because at least one piece can be flipped
                else:  # Either empty or same color without having flipped any
                    break
            else:  # Out of bounds
                break
    return False


def flip_pieces(board, tile, color):
    # Create a deep copy of the board
    new_board = [row[:] for row in board]
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1), (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    opposite_color = 'white' if color == 'black' else 'black'
    # Flip pieces in all valid directions
    for direction in directions:
        tiles_to_flip = []
        for i in range(1, 8):
            x, y = tile[0] + direction[0] * i, tile[1] + direction[1] * i
            if 0 <= x < 8 and 0 <= y < 8:  # Stay within board limits
                current_tile = new_board[x][y]
                if current_tile == opposite_color:
                    tiles_to_flip.append((x, y))
                elif current_tile == color and tiles_to_flip:
                    # Flip the pieces in this direction
                    for flip_tile in tiles_to_flip:
                        new_board[flip_tile[0]][flip_tile[1]] = color
                    break  # Stop checking in this direction after flipping
                else:
                    break  # Either empty or same color without having flipped any
    # Place the new piece
    new_board[tile[0]][tile[1]] = color
    return new_board


def find_changed_positions(old_board, new_board, placed_tile):
    changed_positions = []
    for x in range(len(old_board)):
        for y in range(len(old_board[x])):
            if (x, y) != placed_tile and old_board[x][y] != new_board[x][y]:
                changed_positions.append((x, y))
    return changed_positions
