from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user
from .models import Players, League, GameDay, LeagueClassification, Game, GameDayClassification, GameDayPlayer, ELOranking, ELOrankingHist
from . import db
import json, os, threading
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func, cast, String, text, desc, case, literal_column


views =  Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    try:
        leagues_data = League.query.order_by(League.lg_status, League.lg_endDate.desc()).all()
    except Exception as e:
        print(f"Error: {e}")
    return render_template("index.html", user=current_user, result=leagues_data)

@views.route('/testIndex', methods=['GET', 'POST'])
def testIndex():
    leagues_data = League.query.order_by(League.lg_status, League.lg_endDate.desc()).all()
    return render_template("testIndex.html", user=current_user, result=leagues_data)


@views.route('/players', methods=['GET', 'POST'])
def players():
    players_data = Players.query.order_by(Players.pl_name).all()
    return render_template('players.html', user=current_user, players=players_data)

@views.route('/league/<leagueID>')
def league_detail(leagueID):
    league_data = League.query.filter_by(lg_id=leagueID).first()
    result = GameDay.query.filter_by(gd_idLeague=leagueID).all()
    classification = LeagueClassification.query.filter_by(lc_idLeague=leagueID).order_by(desc(LeagueClassification.lc_ranking)).all()
    return render_template("league_detail.html", user=current_user, league=league_data, result=result, classification=classification) 

@views.route('/gameDay/<gameDayID>')
def gameDay_detail(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    results = Game.query.filter_by(gm_idGameDay=gameDayID).order_by(Game.gm_timeStart).all()
    classifications = GameDayClassification.query.filter_by(gc_idGameDay=gameDayID).order_by(desc(GameDayClassification.gc_ranking)).all()
    return render_template("gameDay_detail.html", user=current_user, gameDay=gameDay_data, result=results, classification=classifications) 

# management
@views.route('/managementLeague', methods=['GET', 'POST'])
@login_required
def managementLeague():
    leagues_data = League.query.order_by(League.lg_status, League.lg_endDate.desc()).all()
    return render_template("managementLeague.html", user=current_user, result=leagues_data)

@views.route('/managementLeague_detail/<leagueID>', methods=['GET', 'POST'])
@login_required
def managementLeague_detail(leagueID):
    league_data = League.query.filter_by(lg_id=leagueID).first()
    result = GameDay.query.filter_by(gd_idLeague=leagueID).all()
    classification = LeagueClassification.query.filter_by(lc_idLeague=leagueID).order_by(desc(LeagueClassification.lc_ranking)).all()
    return render_template("managementLeague_detail.html", user=current_user, league=league_data, result=result, classification=classification)

@views.route('/managementPlayers', methods=['GET', 'POST'])
@login_required
def managementPlayers():
    players_data = Players.query.order_by(Players.pl_name).all()
    return render_template("managementPlayers.html", user=current_user, players=players_data)

@views.route('/rankingELO')
def rankingELO():
    results = db.session.execute(
        text(f"SELECT pl_id, pl_name, ROUND(pl_rankingNow, 2) as pl_rankingNow, ROUND(pl_totalRankingOpo, 2) as pl_totalRankingOpo, pl_wins, pl_losses, pl_totalGames, CASE WHEN instr(pl_name, '\"') > 0 AND instr(substr(pl_name, instr(pl_name, '\"') + 1), '\"') > 0 THEN substr(pl_name, instr(pl_name, '\"') + 1, instr(substr(pl_name, instr(pl_name, '\"') + 1), '\"') - 1) ELSE pl_name END AS pl_name_short FROM tb_ELO_ranking WHERE pl_id in (SELECT pl_id from tb_players where pl_ranking_stat='Y') order by pl_rankingNow desc"),
    ).fetchall()   
    
    return render_template("rankingELO.html", user=current_user, result=results)

@views.route('/create_league', methods=['GET', 'POST'])
@login_required
def create_league():
    # leagues_data = League.query.order_by(League.lg_status).all()
    return render_template("create_league.html", user=current_user)

@views.route('/recalculate_ELO_full')
def recalculate_ELO_full():
    calculate_ELO_full()
    # print("recalculate finished")
    results = db.session.execute(
        text(f"SELECT pl_id, pl_name, ROUND(pl_rankingNow, 2) as pl_rankingNow, ROUND(pl_totalRankingOpo, 2) as pl_totalRankingOpo, pl_wins, pl_losses, pl_totalGames FROM tb_ELO_ranking  order by pl_rankingNow desc"),
    ).fetchall()   
    # print("results loaded")
    # if results:
    #     print("there are results")
    # if current_user:
    #     print("there is user")
    return render_template("rankingELO.html", user=current_user, result=results)

@views.route('/create_game_day/<leagueID>', methods=['GET', 'POST'])
@login_required
def create_game_day(leagueID):
    league_data = League.query.filter_by(lg_id=leagueID).first()
    # leagues_data = League.query.order_by(League.lg_status).all()
    return render_template("create_game_day.html", user=current_user, league=league_data)

@views.route('/create_player', methods=['GET', 'POST'])
@login_required
def create_player():
    return render_template("create_player.html", user=current_user)

@views.route('/delete_player/<playerID>')
@login_required
def delete_player(playerID):
    try:
        # Delete Player
        Players.query.filter_by(pl_id=playerID).delete()

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user
    
    players_data = Players.query.order_by(Players.pl_name).all()
    return render_template('players.html', user=current_user, players=players_data)

@views.route('/deleteLeague/<leagueID>')
@login_required
def deleteLeague(leagueID):
    try:
        # Delete League
        League.query.filter_by(lg_id=leagueID).delete()

        # Commit the changes to the database
        db.session.commit()

        #Delete Gamedays
        GameDay.query.filter(gd_idLeague=leagueID).delete()
        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user
    
    leagues_data = League.query.order_by(League.lg_status, League.lg_endDate.desc()).all()
    return render_template("managementLeague.html", user=current_user, result=leagues_data)

@views.route('/managementGameDay_detail/<gameDayID>')
@login_required
def managementGameDay_detail(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    results = Game.query.filter_by(gm_idGameDay=gameDayID).order_by(Game.gm_timeStart).all()
    classifications = GameDayClassification.query.filter_by(gc_idGameDay=gameDayID).order_by(desc(GameDayClassification.gc_ranking)).all()
    gameDayPlayers = GameDayPlayer.query.filter_by(gp_idGameDay=gameDayID).all()
    number_of_teamsGD = len(gameDayPlayers)
    league = League.query.filter_by(lg_id=gameDay_data.gd_idLeague).first()
    number_of_teams_league = league.lg_nbrTeams
    players_data = Players.query.order_by(Players.pl_name).all()
    league_id = league.lg_id
    gameDay_id = gameDayID
    playersGameDay = GameDayPlayer.query.filter_by(gp_idGameDay=gameDayID).order_by(GameDayPlayer.gp_team.asc(), GameDayPlayer.gp_id.asc()).all()
    # Organize players by team
    teams = {}
    for player in playersGameDay:
        if player.gp_team not in teams:
            teams[player.gp_team] = []
        teams[player.gp_team].append(player)
    return render_template("managementGameDay_detail.html", user=current_user, gameDay=gameDay_data, result=results, classification=classifications, number_of_teamsGD=number_of_teamsGD, number_of_teams_league=number_of_teams_league, players_data=players_data, gameDayPlayers=gameDayPlayers, league_id=league_id, gameDay_id=gameDay_id, teams=teams) 

@views.route('/print_page/<gameDayID>')
@login_required
def print_page(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    league_id = gameDay_data.gd_idLeague
    # Get Title League
    try:
        league_detail = db.session.execute(
            text(f"SELECT lg_name FROM tb_league WHERE lg_id=:lg_id"),
            {"lg_id": league_id}
        ).fetchone()
        leagueName = league_detail[0]
    except Exception as e:
        print("Error1:", e)

    # Get Title GameDay
    try:
        results0 = db.session.execute(
            text(f"SELECT gd_id FROM tb_gameday WHERE gd_idLeague=:lg_id ORDER BY gd_date ASC"),
            {"lg_id": league_id},
        ).fetchall()
        num_jornada = 0
        gameDayName = ""
        for data0 in results0:
            num_jornada += 1
            if str(data0[0]) == gameDayID:
                gameDayName = f"{num_jornada}ª Jornada"
    except Exception as e:
        print("Error2:", e)

    # Get Teams
    try:
        teams = db.session.execute(
            text(f"SELECT gp_namePlayer FROM tb_gameDayPlayer WHERE gp_idLeague=:lg_id AND gp_idGameDay=:gd_id ORDER BY gp_team ASC"),
            {"lg_id": league_id, "gd_id": gameDayID},
        ).fetchall()
        teamA = teams[0][0] + " / " + teams[1][0]
        teamB = teams[2][0] + " / " + teams[3][0]
        teamC = teams[4][0] + " / " + teams[5][0]
        teamD = teams[6][0] + " / " + teams[7][0]
    except Exception as e:
        print("Error3:", e)
    games = Game.query.filter_by(gm_idGameDay=gameDayID).all()
    # Get Games of Gameday
    try:
        games = db.session.execute(
            text(f"SELECT gm_court, gm_timeStart, gm_timeEnd, gm_namePlayer_A1 || ' / ' || gm_namePlayer_A2 as teamA, gm_namePlayer_B1 || ' / ' || gm_namePlayer_B2 as teamB FROM tb_game WHERE gm_idLeague=:lg_id AND gm_idGameDay=:gd_id ORDER BY gm_date DESC, gm_timeStart ASC, gm_id ASC"),
            {"lg_id": league_id, "gd_id": gameDayID},
        ).fetchall()
    except Exception as e:
        print("Error:", e)
    # DONE - Add logic for printing page
    return render_template('print_page.html', gameday=gameDay_data, leagueName=leagueName, gameDayName=gameDayName, teamA=teamA, teamB=teamB, teamC=teamC, teamD=teamD, games=games)

@views.route('/delete_game_day_players/<gameDayID>')
@login_required
def delete_game_day_players(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    leagueID = gameDay_data.gd_idLeague
    # DONE - Add logic for deleting game day players
    try:
        # Delete games associated with the game day
        Game.query.filter_by(gm_idGameDay=gameDayID).delete()
        # Delete game day players associated with the game day
        GameDayPlayer.query.filter_by(gp_idGameDay=gameDayID).delete()

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user

    #Calculate the league classification after
    calculateLeagueClassification(leagueID)
    
    return redirect(url_for('views.managementGameDay_detail', gameDayID=gameDayID)) 


@views.route('/insert_game_day_players/<gameDayID>', methods=['GET', 'POST'])
@login_required
def insert_game_day_players(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    leagueID = gameDay_data.gd_idLeague
    # DONE - Add logic for inserting game day players
    league_id = request.form.get('leagueId')
    # gameDay_id = request.form.get('gameDayId')
    gameDay_id = gameDayID
    type_of_teams = request.form.get('defineTeams')
    alpha_arr = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    league_info = League.query.with_entities(League.lg_nbrTeams).filter_by(lg_id=league_id).first()
    if league_info:
        num_players = league_info[0] * 2
    else:
        num_players = 0

    # before doing anything we should delete all the players from the gameday and update classification
    func_delete_gameday_players_upd_class(gameDayID)

    # check if games are created and if not, create them
    func_create_games_for_gameday(gameDayID)

    if type_of_teams == 'ranking':
        num_rankings = LeagueClassification.query.filter_by(lc_idLeague=league_id).count()
        if num_rankings == 0:
            type_of_teams = 'random'


    # FOR RANKING *************************************************************************************
    if type_of_teams == 'ranking':
        players_array = []
        for i in range(num_players):
            id_player = i + 1
            request_player = f"player{id_player}"
            player_id = request.form[request_player]
            # Get Ranking from player
            player_ranking = 0
            try:
                ranking_info = db.session.execute(
                    text(f"SELECT lc_ranking FROM tb_leagueClassification WHERE lc_idLeague=:league_id and lc_idPlayer=:player_id"),
                    {"league_id": league_id, "player_id": player_id}
                ).fetchone()
                if ranking_info:
                    player_ranking = ranking_info[0] * 100            
            except Exception as e:
                print("Error:", e)

            # if ranking is 0 we assume age/100 as ranking
            if player_ranking==0:
                player = Players.query.filter_by(pl_id=player_id).first()
                if player:
                    # print("Reached here")
                    player_birthday = player.pl_birthday
                    player_age = calculate_player_age(player_birthday)
                    player_ranking = player_age/100  
                    # print(f"Reached here: player_age={player_age}, player_ranking={player_ranking}")              

            players_array.append({"id": player_id, "ranking": player_ranking})

        
        players_array.sort(key=lambda x: x["ranking"], reverse=True)

        try:
            # Delete all existing records on tb_gameDayPlayer
            db.session.execute(
                text(f"DELETE FROM tb_gameDayPlayer WHERE gp_idLeague=:league_id and gp_idGameDay=:gameDay_id"),
                {"league_id": league_id, "gameDay_id": gameDay_id}
            )
            db.session.commit()
        except Exception as e:
            print("Error DELETE tb_gameDayPlayer:", e)

        num_teams = num_players // 2
        for j in range(num_teams):
            team_name = chr(ord('A') + j)

            player1_result = players_array.pop(0)
            player1_team_id = player1_result['id']
            player1_team_name = Players.query.get(player1_team_id).pl_name

            player2_result = players_array.pop()
            player2_team_id = player2_result['id']
            player2_team_name = Players.query.get(player2_team_id).pl_name

            for player_id, player_name in [(player1_team_id, player1_team_name), (player2_team_id, player2_team_name)]:
                try:
                    game_day_player = GameDayPlayer(
                        gp_idLeague=league_id,
                        gp_idGameDay=gameDay_id,
                        gp_idPlayer=player_id,
                        gp_namePlayer=player_name,
                        gp_team=team_name
                    )
                    db.session.add(game_day_player)
                    db.session.commit()
                except Exception as e:
                    print("Error:", e)


            # go through all the teams in GameDayPlayer
            gd_players = GameDayPlayer.query.filter_by(gp_idGameDay=gameDay_id).order_by(GameDayPlayer.gp_team.asc(), GameDayPlayer.gp_id.asc()).all()
    
            # Organize players by team
            teams = {}
            for gd_player in gd_players:
                if gd_player.gp_team not in teams:
                    teams[gd_player.gp_team] = []
                teams[gd_player.gp_team].append(gd_player)

            
            for team, players in teams.items():
                player1ID=0
                player1Name=''
                player2ID=0
                player2Name=''
                for player in players:
                    if player1ID==0:
                        player1ID = player.gp_idPlayer
                        player1Name = player.gp_namePlayer
                    else:
                        player2ID = player.gp_idPlayer
                        player2Name = player.gp_namePlayer

                #print(f"Reached here: {player1ID}, {player1Name}, {player2ID}, {player2Name}, {gameDay_id}, {team}, ")
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_A1=:player1ID, gm_namePlayer_A1=:player1Name, gm_idPlayer_A2=:player2ID, gm_namePlayer_A2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamA=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_B1=:player1ID, gm_namePlayer_B1=:player1Name, gm_idPlayer_B2=:player2ID, gm_namePlayer_B2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamB=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()

    # FOR RANDOM*******************************************************************************                
    elif type_of_teams == 'random':
        # Fill the players_array with the players selected in the page
        players_array = []
        for i in range(num_players):
            id_player = i + 1
            request_player = f"player{id_player}"
            player_id = request.form[request_player]
            players_array.append(player_id)

        try:
            # Delete every player from tb_gameDayPlayer for that gameday
            GameDayPlayer.query.filter_by(gp_idLeague=league_id, gp_idGameDay=gameDay_id).delete()
            db.session.commit()
        except Exception as e:
            print("Error Delete:", e)

        import random
        random.shuffle(players_array)

        num_teams = num_players // 2
        for j in range(num_teams):
            team_name = chr(ord('A') + j)

            player1_team_id = players_array.pop(0)
            player1_team_name = Players.query.get(player1_team_id).pl_name

            player2_team_id = players_array.pop()
            player2_team_name = Players.query.get(player2_team_id).pl_name

            for player_id, player_name in [(player1_team_id, player1_team_name), (player2_team_id, player2_team_name)]:
                try:
                    game_day_player = GameDayPlayer(
                        gp_idLeague=league_id,
                        gp_idGameDay=gameDay_id,
                        gp_idPlayer=player_id,
                        gp_namePlayer=player_name,
                        gp_team=team_name
                    )
                    db.session.add(game_day_player)
                    db.session.commit()
                except Exception as e:
                    print(f"Error: {e}")

            # go through all the teams in GameDayPlayer
            gd_players = GameDayPlayer.query.filter_by(gp_idGameDay=gameDay_id).order_by(GameDayPlayer.gp_team.asc(), GameDayPlayer.gp_id.asc()).all()
    
            # Organize players by team
            teams = {}
            for gd_player in gd_players:
                if gd_player.gp_team not in teams:
                    teams[gd_player.gp_team] = []
                teams[gd_player.gp_team].append(gd_player)

            
            for team, players in teams.items():
                player1ID=0
                player1Name=''
                player2ID=0
                player2Name=''
                for player in players:
                    if player1ID==0:
                        player1ID = player.gp_idPlayer
                        player1Name = player.gp_namePlayer
                    else:
                        player2ID = player.gp_idPlayer
                        player2Name = player.gp_namePlayer

                #print(f"Reached here: {player1ID}, {player1Name}, {player2ID}, {player2Name}, {gameDay_id}, {team}, ")
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_A1=:player1ID, gm_namePlayer_A1=:player1Name, gm_idPlayer_A2=:player2ID, gm_namePlayer_A2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamA=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_B1=:player1ID, gm_namePlayer_B1=:player1Name, gm_idPlayer_B2=:player2ID, gm_namePlayer_B2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamB=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()

    # FOR MANUAL*************************************************************************************
    elif type_of_teams == 'manual':
        players_array = []
        for i in range(num_players):
            id_player = i + 1
            request_player = f"player{id_player}"
            player_id = request.form[request_player]
            players_array.append(player_id)

        try:
            # Delete every player from tb_gameDayPlayer for that gameday
            db.session.execute(
                text(f"DELETE FROM tb_gameDayPlayer WHERE gp_idLeague=:league_id and gp_idGameDay=:gameDay_id"),
                {"league_id": league_id, "gameDay_id": gameDay_id}
            )
            db.session.commit()
        except Exception as e:
            print("Error Delete:", e)

        num_teams = num_players // 2
        for j in range(num_teams):
            team_name = chr(ord('A') + j)

            player1_team_id = players_array.pop(0)
            player1_team_name = Players.query.get(player1_team_id).pl_name

            player2_team_id = players_array.pop(0)
            player2_team_name = Players.query.get(player2_team_id).pl_name

            for player_id, player_name in [(player1_team_id, player1_team_name), (player2_team_id, player2_team_name)]:
                try:
                    game_day_player = GameDayPlayer(
                        gp_idLeague=league_id,
                        gp_idGameDay=gameDay_id,
                        gp_idPlayer=player_id,
                        gp_namePlayer=player_name,
                        gp_team=team_name
                    )
                    db.session.add(game_day_player)
                    db.session.commit()
                except Exception as e:
                    print("Error:", e)

            # go through all the teams in GameDayPlayer
            gd_players = GameDayPlayer.query.filter_by(gp_idGameDay=gameDay_id).order_by(GameDayPlayer.gp_team.asc(), GameDayPlayer.gp_id.asc()).all()
    
            # Organize players by team
            teams = {}
            for gd_player in gd_players:
                if gd_player.gp_team not in teams:
                    teams[gd_player.gp_team] = []
                teams[gd_player.gp_team].append(gd_player)

            
            for team, players in teams.items():
                player1ID=0
                player1Name=''
                player2ID=0
                player2Name=''
                for player in players:
                    if player1ID==0:
                        player1ID = player.gp_idPlayer
                        player1Name = player.gp_namePlayer
                    else:
                        player2ID = player.gp_idPlayer
                        player2Name = player.gp_namePlayer

                #print(f"Reached here: {player1ID}, {player1Name}, {player2ID}, {player2Name}, {gameDay_id}, {team}, ")
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_A1=:player1ID, gm_namePlayer_A1=:player1Name, gm_idPlayer_A2=:player2ID, gm_namePlayer_A2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamA=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()
                db.session.execute(
                text(f"update tb_game set gm_idPlayer_B1=:player1ID, gm_namePlayer_B1=:player1Name, gm_idPlayer_B2=:player2ID, gm_namePlayer_B2=:player2Name where gm_idGameDay=:gameDay_id and gm_teamB=:team"),
                    {"player1ID": player1ID, "player1Name": player1Name, "player2ID": player2ID, "player2Name": player2Name, "gameDay_id": gameDay_id, "team": team}
                )
                db.session.commit()
    
    return redirect(url_for('views.managementGameDay_detail', gameDayID=gameDayID)) 

@views.route('/insertGameDay/<leagueID>', methods=['GET', 'POST'])
@login_required
def insertGameDay(leagueID):
    print("Here")
    try:
        league_id = leagueID
        #TODO - Read from league the number of teams and put into gameDay_teamNum
        leagueInfo = db.session.execute(text(f"SELECT lg_nbrTeams, lg_minWarmUp, lg_minPerGame, lg_minBetweenGames FROM tb_league WHERE lg_id=:league_id"), {'league_id': league_id}).fetchone()
        gameDay_teamNum = leagueInfo[0]
        gameDay_date = request.form.get('gameDay_dateStart')
        gameDay_time = request.form.get('gameDay_timeStart')
        warm_up = leagueInfo[1]
        minPerGame = leagueInfo[2]
        minBetweenGames = leagueInfo[3]
        first_game_time_start = gameDay_time+warm_up
        first_game_time_end = first_game_time_start+minPerGame
        second_game_time_start = first_game_time_end+minBetweenGames
        second_game_time_end = second_game_time_start+minPerGame
        third_game_time_start = second_game_time_end+minBetweenGames
        third_game_time_end = third_game_time_start+minPerGame
        

        # $query = "INSERT INTO tb_gameday (gd_id, gd_idLeague, gd_teamNum, gd_date, gd_status, gd_idWinner1, gd_nameWinner1, gd_idWinner2, gd_nameWinner2, gd_gameDayName) VALUES (NULL, '".$league_id."', '".$gameDay_teamNum."', '".$gameDay_date."', 'Por Jogar', NULL, NULL, NULL, NULL, NULL)";
        db.session.execute(
            text("INSERT INTO tb_gameday (gd_id, gd_idLeague, gd_teamNum, gd_date, gd_status, gd_idWinner1, gd_nameWinner1, gd_idWinner2, gd_nameWinner2, gd_gameDayName) VALUES (NULL, :league_id, :gameDay_teamNum, :gameDay_date, 'Por Jogar', NULL, NULL, NULL, NULL, NULL)"),
            {"league_id": league_id, "gameDay_teamNum": gameDay_teamNum, "gameDay_date": gameDay_date}
        )
        db.session.commit()

        #TODO - taking in consideration the start date and time and all the times in league we can create the placeholdes for the games if they don't exist yet

    except Exception as e:
        print("Error: " + str(e))

    league_data = League.query.filter_by(lg_id=leagueID).first()
    result = GameDay.query.filter_by(gd_idLeague=leagueID).all()
    classification = LeagueClassification.query.filter_by(lc_idLeague=leagueID).order_by(desc(LeagueClassification.lc_ranking)).all()
    return render_template("managementLeague_detail.html", user=current_user, league=league_data, result=result, classification=classification)


@views.route('/player_detail/<playerID>')
def player_detail(playerID):
    current_Player = Players.query.filter_by(pl_id=playerID).first()
    # Define the cutoff date
    cutoff_date = datetime.strptime('2020-01-01', '%Y-%m-%d').date()
    num_game_day_won = db.session.query(func.count()).filter(
        ((GameDay.gd_idWinner1 == playerID) | (GameDay.gd_idWinner2 == playerID)) &
        (GameDay.gd_date > cutoff_date)
    ).scalar()
    if num_game_day_won>0:
        num_game_day_won_text = f"Vencedor de {num_game_day_won} eventos!"
    else:
        num_game_day_won_text = f"Ainda não venceu nenhum evento!"
    
    last_game_date = db.session.query(Game.gm_date).filter(
        ((Game.gm_idPlayer_A1 == playerID) |
        (Game.gm_idPlayer_A2 == playerID) |
        (Game.gm_idPlayer_B1 == playerID) |
        (Game.gm_idPlayer_B2 == playerID)) & (Game.gm_date > cutoff_date)
    ).order_by(Game.gm_date.desc()).first()
    if last_game_date:
        last_game_date_string = last_game_date[0].strftime('%Y-%m-%d')
    else:
        last_game_date_string = "Ainda não tem jogos registados!"

    # All games
    try:
        games_query = db.session.execute(
            text(f"SELECT gm_timeStart, gm_timeEnd, gm_court, CASE WHEN instr(gm_namePlayer_A1, '\"') > 0 AND instr(substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1, instr(substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_A1 END AS gm_namePlayer_A1, CASE WHEN instr(gm_namePlayer_A2, '\"') > 0 AND instr(substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1, instr(substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_A2 END AS gm_namePlayer_A2, gm_result_A, gm_result_B, CASE WHEN instr(gm_namePlayer_B1, '\"') > 0 AND instr(substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1, instr(substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_B1 END AS gm_namePlayer_B1, CASE WHEN instr(gm_namePlayer_B2, '\"') > 0 AND instr(substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1, instr(substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_B2 END AS gm_namePlayer_B2, gm_id, gm_idPlayer_A1, gm_idPlayer_A2, gm_idPlayer_B1, gm_idPlayer_B2, gm_date, (el_afterRank - el_beforeRank) AS gm_points_var FROM tb_game JOIN tb_ELO_ranking_hist ON tb_ELO_ranking_hist.el_gm_id = tb_game.gm_id AND tb_ELO_ranking_hist.el_pl_id = :playerID WHERE (gm_idPlayer_A1 = :playerID OR gm_idPlayer_A2 = :playerID OR gm_idPlayer_B1 = :playerID OR gm_idPlayer_B2 = :playerID) AND (gm_result_A > 0 OR gm_result_B > 0) ORDER BY gm_date DESC, gm_timeStart DESC"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    #Gem games won, lost and totals
    try:
        player_stats = db.session.query(
            ELOranking.pl_wins.label('games_won'),
            ELOranking.pl_losses.label('games_lost'),
            ELOranking.pl_totalGames.label('total_games')
        ).filter(
            ELOranking.pl_id == playerID
        ).first()
    except Exception as e:
        print(f"Error: {str(e)}")

    #Best TeamMate
    try:
        subquery = db.session.query(
            case(
                (and_(Game.gm_idPlayer_A1 == playerID, Game.gm_idPlayer_A2)),
                (and_(Game.gm_idPlayer_A2 == playerID, Game.gm_idPlayer_A1)),
                (and_(Game.gm_idPlayer_B1 == playerID, Game.gm_idPlayer_B2)),
                (and_(Game.gm_idPlayer_B2 == playerID, Game.gm_idPlayer_B1))
            ).label('teamMate'),
            case(
                (and_(Game.gm_idPlayer_A1 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_B1 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_A2 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_B2 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1"))
            ).label('won'),
            case(
                (and_(Game.gm_idPlayer_A1 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_B1 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_A2 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_B2 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1"))
            ).label('lost')
        ).filter(
            (Game.gm_idPlayer_A1 == playerID) |
            (Game.gm_idPlayer_A2 == playerID) |
            (Game.gm_idPlayer_B1 == playerID) |
            (Game.gm_idPlayer_B2 == playerID),
            (Game.gm_result_A > 0) | (Game.gm_result_B > 0),
            (Game.gm_date > cutoff_date)
        ).subquery()

        best_teammate = db.session.query(
            Players.pl_name,
            (func.coalesce(((func.sum(subquery.c.won)*100) / func.count(subquery.c.teamMate)),0)).label('winPerc'),
            func.sum(subquery.c.won).label('won'),
            func.count(subquery.c.teamMate).label('totalgames')
        ).join(
            subquery, subquery.c.teamMate == Players.pl_id
        ).filter(
            Players.pl_ranking_stat == 'Y'
        ).group_by(
            subquery.c.teamMate
        ).order_by(
            desc(func.sum(subquery.c.won) / func.count(subquery.c.teamMate)),
            desc(func.sum(subquery.c.won))
        ).limit(1).first()
        if best_teammate: 
            pass
        else:
            best_teammate=['',0,0,0]


    except Exception as e:
        print(f"Error: {str(e)}")


    # Worst Nightmare
    try:
        worst_nightmare = db.session.execute(
            text(f"SELECT D.oponent as oponent, D.playerName as playerName, D.losses as losses, D.games as games, ((D.losses * 100.0) / D.games) as lostPerc FROM (SELECT C.oponent as oponent, C.losses as losses, (SELECT pl_name FROM tb_players WHERE pl_id=C.oponent) as playerName, (SELECT count() FROM tb_game WHERE (((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND (gm_idPlayer_B1=C.oponent OR gm_idPlayer_B2=C.oponent)) OR ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND (gm_idPlayer_A1=C.oponent OR gm_idPlayer_A2=C.oponent))) AND (gm_result_A>0 OR gm_result_B>0) AND (gm_date > :cutoff_date)) as games FROM (SELECT B.oponent as oponent, B.losses as losses FROM (SELECT A.oponent, count() as losses FROM (SELECT gm_idPlayer_B1 as oponent FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A<gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_B2 as oponent FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A<gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A1 as oponent FROM tb_game WHERE (gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A2 as oponent FROM tb_game WHERE (gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B AND gm_date > :cutoff_date) A GROUP BY A.oponent ORDER BY count(*) DESC) B) C) D ORDER BY ((D.losses * 100.0) / D.games) DESC, D.losses DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if worst_nightmare:
            pass
        else:
            worst_nightmare=['','',0,0,0]

    except Exception as e:
        print(f"Error: {str(e)}")


    #Best Opponent
    try:
        best_opponent = db.session.execute(
            text(f"SELECT E.oponent as oponent, E.playerName as playerName, E.victories as victories, E.games as games, E.victPerc FROM (SELECT D.oponent as oponent, D.playerName as playerName, D.victories as victories, D.games as games, ((D.victories*100)/D.games) as victPerc FROM (SELECT C.oponent as oponent, C.victories as victories, (SELECT pl_name from tb_players where pl_id=C.oponent) as playerName, (SELECT count() from tb_game where (((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) and (gm_idPlayer_B1=C.oponent or gm_idPlayer_B2=C.oponent)) OR ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) and (gm_idPlayer_A1=C.oponent or gm_idPlayer_A2=C.oponent))) and (gm_result_A>0 or gm_result_B>0) and (gm_date > :cutoff_date)) as games FROM ( SELECT B.oponent as oponent, B.victories as victories FROM (SELECT A.oponent, count(*) as victories FROM (SELECT gm_idPlayer_B1 as oponent FROM tb_game where ((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_B2 as oponent FROM tb_game where ((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A1 as oponent FROM tb_game where ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) AND gm_result_A<gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A2 as oponent FROM tb_game where ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) AND gm_result_A<gm_result_B) and gm_date > :cutoff_date) A group by A.oponent) B order by B.victories DESC) C) D inner join tb_players on pl_id=D.oponent where pl_ranking_stat='Y') E ORDER BY E.victPerc DESC, E.victories DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if best_opponent:
            pass
        else:
            best_opponent=['','',0,0,0]
    except Exception as e:
        print(f"Error: {str(e)}")

    #Worst Teammate
    try:
        worst_teammate = db.session.execute(
            text(f"WITH PlayerGames AS ( SELECT CASE WHEN gm_idPlayer_A1=:playerID THEN gm_idPlayer_A2 WHEN gm_idPlayer_A2=:playerID THEN gm_idPlayer_A1 WHEN gm_idPlayer_B1=:playerID THEN gm_idPlayer_B2 WHEN gm_idPlayer_B2=:playerID THEN gm_idPlayer_B1 END AS teamMate, CASE WHEN ((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) THEN 1 WHEN ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_B>gm_result_A) THEN 1 ELSE 0 END AS won, CASE WHEN ((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_B>gm_result_A) THEN 1 WHEN ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B) THEN 1 ELSE 0 END AS lost FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID OR gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND (gm_result_A>0 OR gm_result_B>0) AND (gm_date > :cutoff_date) ) SELECT tb_players.pl_name as pl_name, lostPerc, lost, totalgames FROM ( SELECT teamMate, SUM(won) AS won, SUM(lost) AS lost, COUNT() AS totalgames, SUM(won) / COUNT() AS winPerc, ((SUM(lost)*100) / COUNT(*)) AS lostPerc FROM PlayerGames GROUP BY teamMate ) AS B INNER JOIN tb_players ON tb_players.pl_id = B.teamMate WHERE tb_players.pl_ranking_stat = 'Y' ORDER BY B.lostPerc DESC, B.lost DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if worst_teammate:
            pass
        else:
            worst_teammate=['',0,0,0]

        
    except Exception as e:
        print(f"Error: {str(e)}")

    #Games
    try:
        total_games0 = db.session.execute(
            text(f"SELECT pl_wins AS games_won, pl_totalGames as total_games FROM tb_ELO_ranking where pl_id=:playerID"),
            {"playerID": playerID}
        ).fetchone()
        if total_games0:
            total_games=total_games0
        else:
            total_games = db.session.execute(
                text(f"SELECT COALESCE(SUM(CASE WHEN (g.gm_result_A > g.gm_result_B AND (g.gm_idPlayer_A1 = :playerID OR g.gm_idPlayer_A2 = :playerID)) OR (g.gm_result_B > g.gm_result_A AND (g.gm_idPlayer_B1 = :playerID OR g.gm_idPlayer_B2 = :playerID)) THEN 1 ELSE 0 END), 0) AS total_games_won, COUNT(g.gm_id) AS total_games_played FROM tb_players p LEFT JOIN tb_game g ON p.pl_id IN (g.gm_idPlayer_A1, g.gm_idPlayer_A2, g.gm_idPlayer_B1, g.gm_idPlayer_B2) WHERE p.pl_id = :playerID GROUP BY p.pl_id, p.pl_name;"),
                {"playerID": playerID}
            ).fetchone()
    except Exception as e:
        print(f"Error: {str(e)}")


    # rankingELO_hist
    try:
        rankingELO_hist = db.session.execute(
            text(f"SELECT el_gm_id, el_date, el_startTime, el_pl_name_teammate, el_pl_name_op1, el_pl_name_op2, el_result_team, el_result_op, el_beforeRank, el_afterRank FROM tb_ELO_ranking_hist where el_pl_id=:playerID order by el_date desc, el_startTime desc LIMIT 50"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_hist:
        pass
    else:
        rankingELO_hist=[0,0,0,0,0,0,0,0,0]

    # rankingELO_histShort
    try:
        rankingELO_histShort = db.session.execute(
            text(f"SELECT el_gm_id, el_date, el_startTime, el_pl_name_teammate, el_pl_name_op1, el_pl_name_op2, el_result_team, el_result_op, el_beforeRank, el_afterRank FROM tb_ELO_ranking_hist where el_pl_id=:playerID order by el_date desc, el_startTime desc LIMIT 10"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_histShort:
        pass
    else:
        rankingELO_histShort=[0,0,0,0,0,0,0,0,0]

    # rankingELO_bestWorst
    rankingELO_bestWorst=[1000,1000,1000]
    try:
        rankingELO_bestWorst0 = db.session.execute(
            text(f"SELECT max(el_afterRank) as best, min(el_afterRank) as worst, (SELECT el_afterRank from `tb_ELO_ranking_hist` where el_pl_id=:playerID order by el_date desc, el_startTime desc limit 1) as rankNow FROM `tb_ELO_ranking_hist` where el_pl_id=:playerID"),
            {"playerID": playerID},
        ).fetchone()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_bestWorst0[0]!=None:
        rankingELO_bestWorst = rankingELO_bestWorst0
    else:
        rankingELO_bestWorst=[1000,1000,1000]

    # Splitting the player name based on double quotes
    name_parts = current_Player.pl_name.split('"')

    # Extracting the short name based on the number of parts after splitting
    if len(name_parts) > 1:
        player_name_short = name_parts[1]  # If there is a name enclosed in double quotes
    else:
        player_name_short = name_parts[0]  # If there is no name enclosed in double quotes
    
    # DONE - Get data from games to complete user data
    player_data = {
        "player_id": current_Player.pl_id,
        "player_name": current_Player.pl_name,
        "player_name_short": player_name_short,
        "player_email": current_Player.pl_email,
        "player_birthday": current_Player.pl_birthday,
        "numGameDayWins": num_game_day_won_text,
        "lastGamePlayed": last_game_date_string,
        "games_won": total_games[0],
        "total_games": total_games[1],
        "best_teammate_name": str(best_teammate[0]),
        "best_teammate_win_percentage": "{:.2f}".format(best_teammate[1] ),
        "best_teammate_total_games": best_teammate[3],
        "worst_teammate_name": str(worst_teammate[0]),
        "worst_teammate_lost_percentage": "{:.2f}".format(worst_teammate[1]),
        "worst_teammate_total_games": worst_teammate[3],
        "worst_nightmare_name": str(worst_nightmare[1]) if worst_nightmare else "",
        "worst_nightmare_lost_percentage": "{:.2f}".format(worst_nightmare[4]) if worst_nightmare else 0,
        "worst_nightmare_games": worst_nightmare[3] if worst_nightmare else 0,
        "best_opponent_name": str(best_opponent[1]),
        "best_opponent_victory_percentage": "{:.2f}".format(best_opponent[4]),
        "best_opponent_games": best_opponent[3],
    }
    return render_template("player_detail.html", user=current_user, player_id=playerID, player=player_data, results=games_query, getPlayerStats=player_stats, best_teammate=best_teammate, rankingELO_hist=rankingELO_hist, rankingELO_histShort=rankingELO_histShort, rankingELO_bestWorst=rankingELO_bestWorst)   

@views.route('/player_edit/<playerID>', methods=['GET', 'POST'])
@login_required
def player_edit(playerID):
    current_Player = Players.query.filter_by(pl_id=playerID).first()
    # Define the cutoff date
    cutoff_date = datetime.strptime('2024-01-01', '%Y-%m-%d').date()
    num_game_day_won = db.session.query(func.count()).filter(
        ((GameDay.gd_idWinner1 == playerID) | (GameDay.gd_idWinner2 == playerID)) &
        (GameDay.gd_date > cutoff_date)
    ).scalar()
    if num_game_day_won>0:
        num_game_day_won_text = f"Vencedor de {num_game_day_won} eventos!"
    else:
        num_game_day_won_text = f"Ainda não venceu nenhum evento!"
    
    last_game_date = db.session.query(Game.gm_date).filter(
        ((Game.gm_idPlayer_A1 == playerID) |
        (Game.gm_idPlayer_A2 == playerID) |
        (Game.gm_idPlayer_B1 == playerID) |
        (Game.gm_idPlayer_B2 == playerID)) & (Game.gm_date > cutoff_date)
    ).order_by(Game.gm_date.desc()).first()
    if last_game_date:
        last_game_date_string = last_game_date[0].strftime('%Y-%m-%d')
    else:
        last_game_date_string = "Ainda não tem jogos registados!"

    # # All games
    try:
        games_query = db.session.execute(
            text(f"SELECT gm_timeStart, gm_timeEnd, gm_court, CASE WHEN instr(gm_namePlayer_A1, '\"') > 0 AND instr(substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1, instr(substr(gm_namePlayer_A1, instr(gm_namePlayer_A1, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_A1 END AS gm_namePlayer_A1, CASE WHEN instr(gm_namePlayer_A2, '\"') > 0 AND instr(substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1, instr(substr(gm_namePlayer_A2, instr(gm_namePlayer_A2, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_A2 END AS gm_namePlayer_A2, gm_result_A, gm_result_B, CASE WHEN instr(gm_namePlayer_B1, '\"') > 0 AND instr(substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1, instr(substr(gm_namePlayer_B1, instr(gm_namePlayer_B1, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_B1 END AS gm_namePlayer_B1, CASE WHEN instr(gm_namePlayer_B2, '\"') > 0 AND instr(substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1), '\"') > 0 THEN substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1, instr(substr(gm_namePlayer_B2, instr(gm_namePlayer_B2, '\"') + 1), '\"') - 1) ELSE gm_namePlayer_B2 END AS gm_namePlayer_B2, gm_id, gm_idPlayer_A1, gm_idPlayer_A2, gm_idPlayer_B1, gm_idPlayer_B2, gm_date, (el_afterRank - el_beforeRank) AS gm_points_var FROM tb_game JOIN tb_ELO_ranking_hist ON tb_ELO_ranking_hist.el_gm_id = tb_game.gm_id AND tb_ELO_ranking_hist.el_pl_id = :playerID WHERE (gm_idPlayer_A1 = :playerID OR gm_idPlayer_A2 = :playerID OR gm_idPlayer_B1 = :playerID OR gm_idPlayer_B2 = :playerID) AND (gm_result_A > 0 OR gm_result_B > 0) ORDER BY gm_date DESC, gm_timeStart DESC"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    #Gem games won, lost and totals
    try:
        player_stats = db.session.query(
            ELOranking.pl_wins.label('games_won'),
            ELOranking.pl_losses.label('games_lost'),
            ELOranking.pl_totalGames.label('total_games')
        ).filter(
            ELOranking.pl_id == playerID
        ).first()
    except Exception as e:
        print(f"Error: {str(e)}")

    #Best TeamMate
    try:
        subquery = db.session.query(
            case(
                (and_(Game.gm_idPlayer_A1 == playerID, Game.gm_idPlayer_A2)),
                (and_(Game.gm_idPlayer_A2 == playerID, Game.gm_idPlayer_A1)),
                (and_(Game.gm_idPlayer_B1 == playerID, Game.gm_idPlayer_B2)),
                (and_(Game.gm_idPlayer_B2 == playerID, Game.gm_idPlayer_B1))
            ).label('teamMate'),
            case(
                (and_(Game.gm_idPlayer_A1 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_B1 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_A2 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_B2 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1"))
            ).label('won'),
            case(
                (and_(Game.gm_idPlayer_A1 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_B1 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                (and_(Game.gm_idPlayer_A2 == playerID) & (Game.gm_result_B > Game.gm_result_A), literal_column("1")),
                (and_(Game.gm_idPlayer_B2 == playerID) & (Game.gm_result_A > Game.gm_result_B), literal_column("1"))
            ).label('lost')
        ).filter(
            (Game.gm_idPlayer_A1 == playerID) |
            (Game.gm_idPlayer_A2 == playerID) |
            (Game.gm_idPlayer_B1 == playerID) |
            (Game.gm_idPlayer_B2 == playerID),
            (Game.gm_result_A > 0) | (Game.gm_result_B > 0),
            (Game.gm_date > cutoff_date)
        ).subquery()

        best_teammate = db.session.query(
            Players.pl_name,
            (func.coalesce(((func.sum(subquery.c.won)*100) / func.count(subquery.c.teamMate)),0)).label('winPerc'),
            func.sum(subquery.c.won).label('won'),
            func.count(subquery.c.teamMate).label('totalgames')
        ).join(
            subquery, subquery.c.teamMate == Players.pl_id
        ).filter(
            Players.pl_ranking_stat == 'Y'
        ).group_by(
            subquery.c.teamMate
        ).order_by(
            desc(func.sum(subquery.c.won) / func.count(subquery.c.teamMate)),
            desc(func.sum(subquery.c.won))
        ).limit(1).first()
        if best_teammate:
            pass
        else:
            best_teammate=['',0,0,0]

    except Exception as e:
        print(f"Error: {str(e)}")


    # Worst Nightmare
    try:
        worst_nightmare = db.session.execute(
            text(f"SELECT D.oponent as oponent, D.playerName as playerName, D.losses as losses, D.games as games, ((D.losses * 100.0) / D.games) as lostPerc FROM (SELECT C.oponent as oponent, C.losses as losses, (SELECT pl_name FROM tb_players WHERE pl_id=C.oponent) as playerName, (SELECT count() FROM tb_game WHERE (((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND (gm_idPlayer_B1=C.oponent OR gm_idPlayer_B2=C.oponent)) OR ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND (gm_idPlayer_A1=C.oponent OR gm_idPlayer_A2=C.oponent))) AND (gm_result_A>0 OR gm_result_B>0) AND (gm_date > :cutoff_date)) as games FROM (SELECT B.oponent as oponent, B.losses as losses FROM (SELECT A.oponent, count() as losses FROM (SELECT gm_idPlayer_B1 as oponent FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A<gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_B2 as oponent FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A<gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A1 as oponent FROM tb_game WHERE (gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B AND gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A2 as oponent FROM tb_game WHERE (gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B AND gm_date > :cutoff_date) A GROUP BY A.oponent ORDER BY count(*) DESC) B) C) D ORDER BY ((D.losses * 100.0) / D.games) DESC, D.losses DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if worst_nightmare:
            pass
        else:
            worst_nightmare=['','',0,0,0]

    except Exception as e:
        print(f"Error: {str(e)}")


    #Best Opponent
    try:
        best_opponent = db.session.execute(
            text(f"SELECT E.oponent as oponent, E.playerName as playerName, E.victories as victories, E.games as games, E.victPerc FROM (SELECT D.oponent as oponent, D.playerName as playerName, D.victories as victories, D.games as games, ((D.victories*100)/D.games) as victPerc FROM (SELECT C.oponent as oponent, C.victories as victories, (SELECT pl_name from tb_players where pl_id=C.oponent) as playerName, (SELECT count() from tb_game where (((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) and (gm_idPlayer_B1=C.oponent or gm_idPlayer_B2=C.oponent)) OR ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) and (gm_idPlayer_A1=C.oponent or gm_idPlayer_A2=C.oponent))) and (gm_result_A>0 or gm_result_B>0) and (gm_date > :cutoff_date)) as games FROM ( SELECT B.oponent as oponent, B.victories as victories FROM (SELECT A.oponent, count(*) as victories FROM (SELECT gm_idPlayer_B1 as oponent FROM tb_game where ((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_B2 as oponent FROM tb_game where ((gm_idPlayer_A1=:playerID or gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A1 as oponent FROM tb_game where ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) AND gm_result_A<gm_result_B) and gm_date > :cutoff_date UNION ALL SELECT gm_idPlayer_A2 as oponent FROM tb_game where ((gm_idPlayer_B1=:playerID or gm_idPlayer_B2=:playerID) AND gm_result_A<gm_result_B) and gm_date > :cutoff_date) A group by A.oponent) B order by B.victories DESC) C) D inner join tb_players on pl_id=D.oponent where pl_ranking_stat='Y') E ORDER BY E.victPerc DESC, E.victories DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if best_opponent:
            pass
        else:
            best_opponent=['','',0,0,0]
    except Exception as e:
        print(f"Error: {str(e)}")

    #Worst Teammate
    try:
        worst_teammate = db.session.execute(
            text(f"WITH PlayerGames AS ( SELECT CASE WHEN gm_idPlayer_A1=:playerID THEN gm_idPlayer_A2 WHEN gm_idPlayer_A2=:playerID THEN gm_idPlayer_A1 WHEN gm_idPlayer_B1=:playerID THEN gm_idPlayer_B2 WHEN gm_idPlayer_B2=:playerID THEN gm_idPlayer_B1 END AS teamMate, CASE WHEN ((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_A>gm_result_B) THEN 1 WHEN ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_B>gm_result_A) THEN 1 ELSE 0 END AS won, CASE WHEN ((gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID) AND gm_result_B>gm_result_A) THEN 1 WHEN ((gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND gm_result_A>gm_result_B) THEN 1 ELSE 0 END AS lost FROM tb_game WHERE (gm_idPlayer_A1=:playerID OR gm_idPlayer_A2=:playerID OR gm_idPlayer_B1=:playerID OR gm_idPlayer_B2=:playerID) AND (gm_result_A>0 OR gm_result_B>0) AND (gm_date > :cutoff_date) ) SELECT tb_players.pl_name as pl_name, lostPerc, lost, totalgames FROM ( SELECT teamMate, SUM(won) AS won, SUM(lost) AS lost, COUNT() AS totalgames, SUM(won) / COUNT() AS winPerc, ((SUM(lost)*100) / COUNT(*)) AS lostPerc FROM PlayerGames GROUP BY teamMate ) AS B INNER JOIN tb_players ON tb_players.pl_id = B.teamMate WHERE tb_players.pl_ranking_stat = 'Y' ORDER BY B.lostPerc DESC, B.lost DESC LIMIT 1"),
            {"playerID": playerID, "cutoff_date": cutoff_date}
        ).fetchone()
        if worst_teammate:
            pass
        else:
            worst_teammate=['',0,0,0]

        
    except Exception as e:
        print(f"Error: {str(e)}")

    #Games
    try:
        total_games0 = db.session.execute(
            text(f"SELECT pl_wins AS games_won, pl_totalGames as total_games FROM tb_ELO_ranking where pl_id=:playerID"),
            {"playerID": playerID}
        ).fetchone()
        if total_games0:
            total_games=total_games0
        else:
            total_games = db.session.execute(
                text(f"SELECT COALESCE(SUM(CASE WHEN (g.gm_result_A > g.gm_result_B AND (g.gm_idPlayer_A1 = :playerID OR g.gm_idPlayer_A2 = :playerID)) OR (g.gm_result_B > g.gm_result_A AND (g.gm_idPlayer_B1 = :playerID OR g.gm_idPlayer_B2 = :playerID)) THEN 1 ELSE 0 END), 0) AS total_games_won, COUNT(g.gm_id) AS total_games_played FROM tb_players p LEFT JOIN tb_game g ON p.pl_id IN (g.gm_idPlayer_A1, g.gm_idPlayer_A2, g.gm_idPlayer_B1, g.gm_idPlayer_B2) WHERE p.pl_id = :playerID GROUP BY p.pl_id, p.pl_name;"),
                {"playerID": playerID}
            ).fetchone()
    except Exception as e:
        print(f"Error: {str(e)}")

    # rankingELO_hist
    try:
        rankingELO_hist = db.session.execute(
            text(f"SELECT el_gm_id, el_date, el_startTime, el_pl_name_teammate, el_pl_name_op1, el_pl_name_op2, el_result_team, el_result_op, el_beforeRank, el_afterRank FROM tb_ELO_ranking_hist where el_pl_id=:playerID order by el_date desc, el_startTime desc LIMIT 50"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_hist:
        pass
    else:
        rankingELO_hist=[0,0,0,0,0,0,0,0,0]

    # rankingELO_histShort
    try:
        rankingELO_histShort = db.session.execute(
            text(f"SELECT el_gm_id, el_date, el_startTime, el_pl_name_teammate, el_pl_name_op1, el_pl_name_op2, el_result_team, el_result_op, el_beforeRank, el_afterRank FROM tb_ELO_ranking_hist where el_pl_id=:playerID order by el_date desc, el_startTime desc LIMIT 10"),
            {"playerID": playerID},
        ).fetchall()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_histShort:
        pass
    else:
        rankingELO_histShort=[0,0,0,0,0,0,0,0,0]

    # rankingELO_bestWorst
    rankingELO_bestWorst=[1000,1000,1000]
    try:
        rankingELO_bestWorst0 = db.session.execute(
            text(f"SELECT max(el_afterRank) as best, min(el_afterRank) as worst, (SELECT el_afterRank from `tb_ELO_ranking_hist` where el_pl_id=:playerID order by el_date desc, el_startTime desc limit 1) as rankNow FROM `tb_ELO_ranking_hist` where el_pl_id=:playerID"),
            {"playerID": playerID},
        ).fetchone()
    except Exception as e:
        print(f"Error: {str(e)}")

    if rankingELO_bestWorst0[0]!=None:
        rankingELO_bestWorst = rankingELO_bestWorst0
    else:
        rankingELO_bestWorst=[1000,1000,1000]

    # Splitting the player name based on double quotes
    name_parts = current_Player.pl_name.split('"')

    # Extracting the short name based on the number of parts after splitting
    if len(name_parts) > 1:
        player_name_short = name_parts[1]  # If there is a name enclosed in double quotes
    else:
        player_name_short = name_parts[0]  # If there is no name enclosed in double quotes
    
    # DONE - Get data from games to complete user data
    player_data = {
        "player_id": current_Player.pl_id,
        "player_name": current_Player.pl_name,
        "player_name_short": player_name_short,
        "player_email": current_Player.pl_email,
        "player_birthday": current_Player.pl_birthday,
        "player_category": 1000,
        "numGameDayWins": num_game_day_won_text,
        "lastGamePlayed": last_game_date_string,
        "games_won": total_games[0],
        "total_games": total_games[1],
        "best_teammate_name": str(best_teammate[0]),
        "best_teammate_win_percentage": "{:.2f}".format(best_teammate[1] ),
        "best_teammate_total_games": best_teammate[3],
        "worst_teammate_name": str(worst_teammate[0]),
        "worst_teammate_lost_percentage": "{:.2f}".format(worst_teammate[1]* 100),
        "worst_teammate_total_games": worst_teammate[3],
        "worst_nightmare_name": str(worst_nightmare[1]) if worst_nightmare else "",
        "worst_nightmare_lost_percentage": "{:.2f}".format(worst_nightmare[4]) if worst_nightmare else 0,
        "worst_nightmare_games": worst_nightmare[3] if worst_nightmare else 0,
        "best_opponent_name": str(best_opponent[1]),
        "best_opponent_victory_percentage": "{:.2f}".format(best_opponent[4]),
        "best_opponent_games": best_opponent[3],
    }
    return render_template("player_edit.html", user=current_user, player_id=playerID, player=player_data, results=games_query, getPlayerStats=player_stats, best_teammate=best_teammate, rankingELO_hist=rankingELO_hist, rankingELO_histShort=rankingELO_histShort, rankingELO_bestWorst=rankingELO_bestWorst)   


@views.route('/display_user_image/<userID>')
def display_user_image(userID):
    filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/users/'+str(userID)+'/main.jpg'
    if os.path.isfile(filePath):
        return redirect(url_for('static', filename='photos/users/'+ str(userID)+'/main.jpg'), code=301)
    else:
        return redirect(url_for('static', filename='photos/users/nophoto.jpg'), code=301)
    

@views.route('/display_league_image_big/<leagueID>')
def display_league_image_big(leagueID):
    filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'+str(leagueID)+'.jpg'
    if os.path.isfile(filePath):
        return redirect(url_for('static', filename='photos/leagues/'+ str(leagueID)+'.jpg'), code=301)
    else:
        return redirect(url_for('static', filename='photos/leagues/nophoto.jpg'), code=301)
    
@views.route('/display_league_image_small/<leagueID>')
def display_league_image_small(leagueID):
    filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'+str(leagueID)+'s.jpg'
    if os.path.isfile(filePath):
        return redirect(url_for('static', filename='photos/leagues/'+ str(leagueID)+'s.jpg'), code=301)
    else:
        return redirect(url_for('static', filename='photos/leagues/nophotoS.jpg'), code=301)    


@views.route('/submitResultsGameDay/<gameDayID>', methods=['GET', 'POST'])
@login_required
def submitResultsGameDay(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    league_id = gameDay_data.gd_idLeague
    #Get all ids of that gameday
    result = Game.query.filter_by(gm_idGameDay=gameDayID).all()
    if result:
        for data in result:
            resultA = f"resultGameA{data.gm_id}"
            resultB = f"resultGameB{data.gm_id}"
            gameID = data.gm_id
            getResultA = request.form.get(resultA)
            getResultB = request.form.get(resultB)
            db.session.execute(
            text(f"update tb_game set gm_result_A=:getResultA, gm_result_B=:getResultB where gm_id=:gameID and gm_idLeague=:league_id"),
                {"getResultA": getResultA, "getResultB": getResultB, "gameID": gameID, "league_id": league_id}
            )
            db.session.commit()

        db.session.execute(
        text(f"update tb_gameday SET gd_status='Terminado' where gd_id=:gameDayID and gd_idLeague=:league_id"),
            {"gameDayID": gameDayID, "league_id": league_id}
        )
        db.session.commit()

        #If all gamedays of that league are Terminado  change status of League to Terminado
        ended_game_days_count = GameDay.query.filter_by(gd_idLeague=league_id, gd_status='Por Jogar').count()

        if ended_game_days_count == 0:
            # Update the league status to 'Terminado'
            league = League.query.get(league_id)
            league.lg_status = '8 - Terminado'
            db.session.commit()

        calculateGameDayClassification(gameDayID)
        calculateLeagueClassification(league_id)
        calculate_ELO_parcial()

    return redirect(url_for('views.managementGameDay_detail', gameDayID=gameDayID)) 


@views.route('/insertLeague', methods=['GET', 'POST'])
@login_required
def insertLeague():
    league_name = request.form.get('league_name')
    league_level = request.form.get('league_level')
    league_status = request.form.get('league_status')
    league_numGameDays = request.form.get('league_numGameDays')
    league_numTeams = request.form.get('league_teams')
    league_dateStart = request.form.get('league_dateStart')
    league_dateEnd = request.form.get('league_dateEnd')
    league_timeStart_HHMM = request.form.get('timeStart')
    league_type = request.form.get('league_type')
    league_timeStart = league_timeStart_HHMM + ':00'

    # Insert into league
    try:
        if league_type == 'Liga':
            lg_minWarmUp = 5
            lg_minPerGame = 25
            lg_minBetweenGames = 5
            lg_eloK = 40
            db.session.execute(
                text("INSERT INTO tb_league (lg_name, lg_level, lg_status, lg_nbrDays, lg_nbrTeams, lg_startDate, lg_endDate, lg_startTime, lg_typeOfLeague, lg_minWarmUp, lg_minPerGame, lg_minBetweenGames, lg_eloK) VALUES (:league_name, :league_level, :league_status, :league_numGameDays, :league_numTeams, :league_dateStart, :league_dateEnd, :league_timeStart, :league_type, :lg_minWarmUp, :lg_minPerGame, :lg_minBetweenGames, :lg_eloK)"),
                {"league_name": league_name, "league_level": league_level, "league_status": league_status, "league_numGameDays": league_numGameDays, "league_numTeams": league_numTeams, "league_dateStart": league_dateStart, "league_dateEnd": league_dateEnd, "league_timeStart": league_timeStart, "league_type": league_type, "lg_minWarmUp": lg_minWarmUp, "lg_minPerGame": lg_minPerGame, "lg_minBetweenGames": lg_minBetweenGames, "lg_eloK": lg_eloK}
            )
            db.session.commit()
        else:
            league_numGameDays = 0
            league_dateEnd = '9999-12-31'
            lg_minWarmUp = 5
            lg_minPerGame = 25
            lg_minBetweenGames = 5
            lg_eloK = 0
            db.session.execute(
                text("INSERT INTO tb_league (lg_name, lg_level, lg_status, lg_nbrDays, lg_nbrTeams, lg_startDate, lg_endDate, lg_typeOfLeague, lg_minWarmUp, lg_minPerGame, lg_minBetweenGames, lg_eloK) VALUES (:league_name, :league_level, :league_status, :league_numGameDays, :league_numTeams, :league_dateStart, :league_dateEnd, :league_type, :lg_minWarmUp, :lg_minPerGame, :lg_minBetweenGames, :lg_eloK)"),
                {"league_name": league_name, "league_level": league_level, "league_status": league_status, "league_numGameDays": league_numGameDays, "league_numTeams": league_numTeams, "league_dateStart": league_dateStart, "league_dateEnd": league_dateEnd, "league_type": league_type, "lg_minWarmUp": lg_minWarmUp, "lg_minPerGame": lg_minPerGame, "lg_minBetweenGames": lg_minBetweenGames, "lg_eloK": lg_eloK}
            )
            db.session.commit()
    except Exception as e:
        print("Error: " + str(e))
    
    # Retrieve league id for photo
    try:
        #print("reached playerinfo")
        leagueInfo = db.session.execute(
            text(f"SELECT lg_id FROM tb_league WHERE lg_name=:league_name AND lg_level=:league_level AND lg_status=:league_status AND lg_nbrDays=:league_numGameDays AND lg_nbrTeams=:league_numTeams AND lg_startDate=:league_dateStart AND lg_endDate=:league_dateEnd"),
            {"league_name": league_name, "league_level": league_level, "league_status": league_status, "league_numGameDays": league_numGameDays, "league_numTeams": league_numTeams, "league_dateStart": league_dateStart, "league_dateEnd": league_dateEnd}
        ).fetchone()
        #print("executed playerinfo")
        if leagueInfo:
            #print(playerInfo)
            league_id = leagueInfo[0]
            if league_type == 'Liga':
                gameDayInfo = db.session.execute(
                    text(f"SELECT COUNT(*) AS NUMGAMEDAYS FROM tb_gameday WHERE gd_idLeague=:league_id"),
                    {"league_id": league_id}
                ).fetchone()
                numGameDays = gameDayInfo[0]
                # print(f"numGameDays= {numGameDays}")
                # Create
                if numGameDays == 0:
                    # Get league information
                    league_info = League.query.filter_by(lg_id=league_id).first()
                    
                    if league_info:
                        # print("Have league_info")
                        league_nbr_days = league_info.lg_nbrDays
                        league_start_date = league_info.lg_startDate
                        league_end_date = league_info.lg_endDate
                        league_status = league_info.lg_status

                        # next_date = datetime.strptime(league_start_date, '%Y-%m-%d')
                        # next_date = league_start_date
                        league_start_datetime = datetime.strptime(str(league_start_date), '%Y-%m-%d')
                        next_date_time = league_start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                        # print(f"next_date_time= {next_date_time}")

                        for i in range(league_nbr_days):
                            if league_status == "Inativo":
                                game_day_status = "Terminado"
                            else:
                                # if nextDate < today, set status to "Terminado"
                                if next_date_time < datetime.now():
                                    game_day_status = "Terminado"
                                # else, set status to "Por Jogar"
                                else:
                                    game_day_status = "Por Jogar"

                            # Insert game day into the database
                            next_date = next_date_time.date()
                            # print(f"next_date= {next_date}")
                            game_day = GameDay(gd_idLeague=league_id, gd_date=next_date, gd_status=game_day_status)
                            # print("GameDay object")
                            db.session.add(game_day)
                            db.session.commit()
                            # print("Added GameDay")

                            # Increment next date by 7 days
                            next_date_time += timedelta(days=7)
                            # print(f"next_date_time= {next_date_time}")
                    else:
                        print("League not found")
                else:
                    print("Game days already exist for this league")
            #print(f"player_id: {player_id}")
    except Exception as e:
        print("Error: " + str(e))

    # Insert photo of player
    # print("Reached Insert Photo")
    image = request.files['league_billboard']
    if image and league_id>0:
        # print("Reached image exists")
        #image is found")
        # path = 'website/static/photos/leagues/'
        path = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'
        pathRelative = 'static\\photos\\leagues\\'
        filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'+str(league_id)+'.jpg'
        # print(f"Path: {path}")
        # print(f"pathRelative: {pathRelative}")
        # print(f"filePath: {filePath}")
                
        # Check if directory exists, if not, create it.
        if os.path.exists(path) == False:
            # print('Dir path not found')
            os.mkdir(path)
        # Check if main.jpg exists, if exists delete it
        if os.path.exists(filePath) == True:
            os.remove(filePath)
        
        # Upload image to directory
        fileName = str(league_id)+'.jpg'
        basedir = os.path.abspath(os.path.dirname(__file__))
        # print(f"basedir: {basedir}")
        # print(f"filePath: {filePath}")
        newPath = os.path.join(basedir, pathRelative, fileName)
        # image.save(newPath)
        image.save(filePath)
        # print("image saved")

    image_S = request.files['league_billboard_S']
    if image_S and league_id>0:
        #image is found")
        # path = 'website/static/photos/leagues/'
        path = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'
        pathRelative = 'static\\photos\\leagues\\'
        filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/leagues/'+str(league_id)+'s.jpg'
                
        # Check if directory exists, if not, create it.
        if os.path.exists(path) == False:
            #print('Dir path not found')
            os.mkdir(path)
        # Check if main.jpg exists, if exists delete it
        if os.path.exists(filePath) == True:
            os.remove(filePath)
        
        # Upload image to directory
        fileName = str(league_id)+'s.jpg'
        basedir = os.path.abspath(os.path.dirname(__file__))
        #print(f"basedir: {basedir}")
        #print(f"filePath: {filePath}")
        newPath = os.path.join(basedir, pathRelative, fileName)
        # image.save(newPath)
        image_S.save(filePath)
        #print("image saved")


    return redirect(url_for('views.managementLeague', user=current_user)) 

@views.route('/insertPlayer', methods=['GET', 'POST'])
@login_required
def insertPlayer():
    playerName = request.form.get('player_name')
    playerEmail = request.form.get('player_email')
    playerDOB = request.form.get('player_dob')
    playerCat = 1000
    playerPhoto = request.form.get('player_photo')

    
    # print(f"playerName: {playerName}")
    # print(f"playerEmail: {playerEmail}")
    # print(f"playerDOB: {playerDOB}")
    # Check if player already exists
    player_id = 0
    try:
        playerInfo = db.session.execute(
            text(f"SELECT pl_id FROM tb_players WHERE pl_name=:player_name AND (pl_email=:player_email or pl_birthday=:player_dob)"),
            {"player_name": playerName, "player_email": playerEmail, "player_dob": playerDOB}
        ).fetchone()
        if playerInfo:
            # print(f"Player found: {playerInfo}")
            player_id = playerInfo[0]
        else:
            playerInfo = db.session.execute(
                text(f"SELECT pl_id FROM tb_players WHERE pl_name=:player_name AND pl_birthday=:player_dob"),
                {"player_name": playerName, "player_dob": playerDOB}
            ).fetchone()
            if playerInfo:
                # print(f"Player found: {playerInfo}")
                player_id = playerInfo[0]
    except Exception as e:
        print("Error: " + str(e))

    if player_id == 0:
        # Insert into players
        try:
            db.session.execute(
                text(f"INSERT INTO tb_players (pl_name, pl_email, pl_birthday, pl_ranking_stat) VALUES (:player_name, :player_email, :player_dob, :playerCat, 'Y')"),
                {"player_name": playerName, "player_email": playerEmail, "player_dob": playerDOB, "playerCat": playerCat}
            )
            db.session.commit()
        except Exception as e:
            print("Error: " + str(e))
        
        # Retrieve player id for photo
        try:
            #print("reached playerinfo")
            playerInfo = db.session.execute(
                text(f"SELECT pl_id FROM tb_players WHERE pl_name=:player_name AND pl_email=:player_email AND pl_birthday=:player_dob"),
                {"player_name": playerName, "player_email": playerEmail, "player_dob": playerDOB}
            ).fetchone()
            #print("executed playerinfo")
            if playerInfo:
                #print(playerInfo)
                player_id = playerInfo[0]
                #print(f"player_id: {player_id}")
        except Exception as e:
            print("Error: " + str(e))
    else:
        # Update Player
        try:
            db.session.execute(
            text(f"UPDATE tb_players SET pl_name=:player_name, pl_email=:player_email, pl_birthday=:player_dob WHERE pl_id=:player_id"),
                {"player_name": playerName, "player_email": playerEmail, "player_dob": playerDOB, "player_id": player_id, "playerCat": playerCat}
            )
            db.session.commit()
        except Exception as e:
            print("Error: " + str(e))

    # Insert photo of player
    image = request.files['player_photo']
    if image and player_id>0:
        #image is found")
        # path = 'website/static/photos/users/'+str(player_id)+'/'
        path = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/users/'+str(player_id)+'/'
        pathRelative = 'static\\photos\\users\\'+str(player_id)+'\\'
        filePath = str(os.path.abspath(os.path.dirname(__file__)))+'/static/photos/users/'+str(player_id)+'/main.jpg'
                
        # Check if directory exists, if not, create it.
        if os.path.exists(path) == False:
            #print('Dir path not found')
            os.mkdir(path)
        # Check if main.jpg exists, if exists delete it
        if os.path.exists(filePath) == True:
            os.remove(filePath)
        
        # Upload image to directory
        fileName = 'main.jpg'
        basedir = os.path.abspath(os.path.dirname(__file__))
        #print(f"basedir: {basedir}")
        #print(f"filePath: {filePath}")
        newPath = os.path.join(basedir, pathRelative, fileName)
        # image.save(newPath)
        image.save(filePath)
        #print("image saved")


    return redirect(url_for('views.managementPlayers', user=current_user)) 

@views.route('/rankingELOweek', methods=['GET', 'POST'])
def ranking_elo_week():
    # Define the start date
    start_date = datetime.strptime('2022-05-30', '%Y-%m-%d')
    # Get today's date
    today = datetime.now()
    # Calculate the difference in days between today and the start date
    difference = (today - start_date).days
    # Calculate the number of weeks between the start date and today
    num_weeks = difference // 7
    # Generate an array to store the Mondays
    mondays = []
    # Iterate over the number of weeks and calculate each Monday
    for i in range(num_weeks + 1):
        monday = start_date + timedelta(days=i * 7)
        mondays.append(monday.strftime('%Y-%m-%d'))

    # Reverse the array to have the Mondays in ascending order
    mondays.reverse()
    if request.method == 'POST':
        selectedMonday = request.form.get('selectedMonday')
        # Parse the selectedMonday as needed
        previousMondayDisabled = request.form.get('previousMondayDisabled')
        nextMondayDisabled = request.form.get('nextMondayDisabled')
        # Handle the form submission and process the data
        # ...
    else:
        # Get today's date
        today = datetime.now()
        # Calculate the difference in days between today and the last Monday
        difference = today.weekday() - 0  # Monday is 0 in Python's datetime module
        # If today is Monday, set the difference to 7 to get the same date
        if difference < 0:
            difference += 7
        # Calculate the last Monday
        last_monday = today - timedelta(days=difference)
        # Format the last Monday as YYYY-MM-DD
        selectedMonday = last_monday.strftime('%Y-%m-%d')
        previousMondayDisabled = ""
        nextMondayDisabled = "disabled"


    results = db.session.execute(
        text(
            "SELECT p.pl_id AS pl_id, p.pl_name as pl_name, "
            "CASE "
            "WHEN instr(p.pl_name, '\"') > 0 AND instr(substr(p.pl_name, instr(p.pl_name, '\"') + 1), '\"') > 0 THEN "
            " substr(p.pl_name, instr(p.pl_name, '\"') + 1, instr(substr(p.pl_name, instr(p.pl_name, '\"') + 1), '\"') - 1)"
            "ELSE p.pl_name "
            "END AS pl_name_short, "
            "ROUND(e.el_AfterRank, 2) as pl_rankingNow "
            "FROM tb_players p "
            "LEFT JOIN tb_ELO_ranking_hist e ON p.pl_id = e.el_pl_id "
            "WHERE (e.el_date, e.el_startTime) = ( "
            "SELECT e2.el_date, e2.el_startTime "
            "FROM tb_ELO_ranking_hist e2 "
            "WHERE e2.el_pl_id = p.pl_id "
            "AND e2.el_date <= :selectedMonday "
            "ORDER BY e2.el_date DESC, e2.el_startTime DESC "
            "LIMIT 1) "
            "AND pl_ranking_stat='Y' "
            "ORDER BY pl_rankingNow DESC"
        ),
        {"selectedMonday": selectedMonday}
    ).fetchall()

    return render_template('rankingELOweek.html', user=current_user, mondays=mondays, selectedMonday=selectedMonday, result=results, previousMondayDisabled=previousMondayDisabled, nextMondayDisabled=nextMondayDisabled)


def calculateLeagueClassification(leagueID):
    #print("Enter LeagueClassification")
    # clear the league classification
    try:
        LeagueClassification.query.filter_by(lc_idLeague=leagueID).delete()
        db.session.commit()

        players_query = Players.query.filter(Players.pl_id.in_(db.session.query(GameDayPlayer.gp_idPlayer).filter(GameDayPlayer.gp_idLeague == leagueID).group_by(GameDayPlayer.gp_idPlayer)))
        players_data = players_query.all()


        for player in players_data:
            id_player = player.pl_id
            player_name = player.pl_name
            player_birthday = player.pl_birthday
            player_age = calculate_player_age(player_birthday)

            games_info_query = Game.query.filter(Game.gm_idLeague == leagueID, ((Game.gm_idPlayer_A1 == id_player) | (Game.gm_idPlayer_A2 == id_player) | (Game.gm_idPlayer_B1 == id_player) | (Game.gm_idPlayer_B2 == id_player)), ((Game.gm_result_A > 0) | (Game.gm_result_B > 0)))
            games_info = games_info_query.first()

            if games_info:
                subquery = (
                    db.session.query(
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("3")),
                            else_=None
                        ).label("POINTS"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_A2 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_B1 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_B2 == id_player), Game.gm_result_B),
                            else_=None
                        ).label("GAMESFAVOR"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_A2 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_B1 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_B2 == id_player), Game.gm_result_A),
                            else_=None
                        ).label("GAMESAGAINST"),
                        literal_column("1").label("GAMES"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            else_=None
                        ).label("WINS"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            else_=None
                        ).label("LOSSES")
                    )
                    .filter(Game.gm_idLeague == leagueID, (Game.gm_idPlayer_A1 == id_player) | (Game.gm_idPlayer_A2 == id_player) | (Game.gm_idPlayer_B1 == id_player) | (Game.gm_idPlayer_B2 == id_player))
                    .subquery("TOTALS")
                )

                query = (
                    db.session.query(
                        literal_column(str(leagueID)).label("LEAGUEID"),
                        literal_column(str(id_player)).label("PLAYERID"),
                        literal_column(f"'{player_name}'").label("PLAYERNAME"), 
                        # TODO - if it is to give one point per participation leave like this, otherwise get this in a config file
                        # (func.sum(subquery.c.POINTS)+(func.sum(subquery.c.GAMES)/3)).label("POINTS"),
                        (func.sum(subquery.c.POINTS)).label("POINTS"),
                        func.sum(subquery.c.WINS).label("WINS"),
                        func.sum(subquery.c.LOSSES).label("LOSSES"),
                        func.sum(subquery.c.GAMESFAVOR).label("GAMESFAVOR"),
                        func.sum(subquery.c.GAMESAGAINST).label("GAMESAGAINST"),
                        (func.sum(subquery.c.GAMESFAVOR) - func.sum(subquery.c.GAMESAGAINST)).label("GAMESDIFFERENCE"),
                        (
                            ((func.sum(subquery.c.POINTS) + func.sum(subquery.c.GAMES) / 3) * 100000) +
                            (func.sum(subquery.c.WINS) *10000) +
                            (func.sum(subquery.c.GAMES) *1000) +
                            ((func.sum(subquery.c.GAMESFAVOR)- func.sum(subquery.c.GAMESAGAINST))*100) +
                            # ((func.sum(subquery.c.WINS) / func.sum(subquery.c.GAMES)) * 10000) +
                            # ((func.sum(subquery.c.GAMESFAVOR) / (func.sum(subquery.c.GAMESFAVOR) + func.sum(subquery.c.GAMESAGAINST))) * 100) +
                            (player_age / 100)
                        ).label("RANKING")
                    )
                    .select_from(subquery)
                    .group_by("LEAGUEID", "PLAYERID", "PLAYERNAME")
                )

                result = query.all()

                for r2 in result:
                    # Write Classification
                    classification = LeagueClassification(
                        lc_idLeague=leagueID,
                        lc_idPlayer=r2.PLAYERID,
                        lc_namePlayer=r2.PLAYERNAME,
                        lc_points=r2.POINTS or 0,
                        lc_wins=r2.WINS or 0,
                        lc_losses=r2.LOSSES or 0,
                        lc_gamesFavor=r2.GAMESFAVOR or 0,
                        lc_gamesAgainst=r2.GAMESAGAINST or 0,
                        lc_gamesDiff=r2.GAMESDIFFERENCE or 0,
                        lc_ranking=r2.RANKING or 0,
                    )
                    db.session.add(classification)

                # Commit the changes to the database
                db.session.commit()

            else:
                # Calculation for players without games
                # Write Classification
                classification = LeagueClassification(
                    lc_idLeague=leagueID,
                    lc_idPlayer=id_player,
                    lc_namePlayer=player_name,
                    lc_points=0,
                    lc_wins=0,
                    lc_losses=0,
                    lc_gamesFavor=0,
                    lc_gamesAgainst=0,
                    lc_gamesDiff=0,
                    lc_ranking=0+(player_age/100),
                )
                db.session.add(classification)
                db.session.commit()

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user

def calculateGameDayClassification(gameDayID):
    #print("Enter GameDayClassification")
    # clear the league classification
    gameDay = GameDay.query.filter_by(gd_id=gameDayID).first()
    leagueID = gameDay.gd_idLeague
    try:
        GameDayClassification.query.filter_by(gc_idGameDay=gameDayID).delete()
        db.session.commit()

        players_query = Players.query.filter(Players.pl_id.in_(db.session.query(GameDayPlayer.gp_idPlayer).filter(GameDayPlayer.gp_idGameDay == gameDayID).group_by(GameDayPlayer.gp_idPlayer)))
        players_data = players_query.all()


        for player in players_data:
            #print(player)
            id_player = player.pl_id
            player_name = player.pl_name
            player_birthday = player.pl_birthday
            player_age = calculate_player_age(player_birthday)

            games_info_query = Game.query.filter(Game.gm_idGameDay == gameDayID, ((Game.gm_idPlayer_A1 == id_player) | (Game.gm_idPlayer_A2 == id_player) | (Game.gm_idPlayer_B1 == id_player) | (Game.gm_idPlayer_B2 == id_player)), ((Game.gm_result_A > 0) | (Game.gm_result_B > 0)))
            games_info = games_info_query.first()

            if games_info:
                subquery = (
                    db.session.query(
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("3")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("3")),
                            else_=None
                        ).label("POINTS"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_A2 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_B1 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_B2 == id_player), Game.gm_result_B),
                            else_=None
                        ).label("GAMESFAVOR"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_A2 == id_player), Game.gm_result_B),
                            (and_(Game.gm_idPlayer_B1 == id_player), Game.gm_result_A),
                            (and_(Game.gm_idPlayer_B2 == id_player), Game.gm_result_A),
                            else_=None
                        ).label("GAMESAGAINST"),
                        literal_column("1").label("GAMES"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            else_=None
                        ).label("WINS"),
                        case(
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_A1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_A2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A > Game.gm_result_B), literal_column("1")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A == Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B1 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            (and_(Game.gm_idPlayer_B2 == id_player, Game.gm_result_A < Game.gm_result_B), literal_column("0")),
                            else_=None
                        ).label("LOSSES")
                    )
                    .filter(Game.gm_idGameDay == gameDayID, (Game.gm_idPlayer_A1 == id_player) | (Game.gm_idPlayer_A2 == id_player) | (Game.gm_idPlayer_B1 == id_player) | (Game.gm_idPlayer_B2 == id_player))
                    .subquery("TOTALS")
                )
                
                query = (
                    db.session.query(
                        literal_column(str(leagueID)).label("LEAGUEID"),
                        literal_column(str(gameDayID)).label("GAMEDAYID"),
                        literal_column(str(id_player)).label("PLAYERID"),
                        literal_column(f"'{player_name}'").label("PLAYERNAME"), 
                        # TODO - if it is to give one point per participation leave like this, otherwise get this in a config file
                        # (func.sum(subquery.c.POINTS)+(func.sum(subquery.c.GAMES)/3)).label("POINTS"),
                        (func.sum(subquery.c.POINTS)).label("POINTS"),
                        func.sum(subquery.c.WINS).label("WINS"),
                        func.sum(subquery.c.LOSSES).label("LOSSES"),
                        func.sum(subquery.c.GAMESFAVOR).label("GAMESFAVOR"),
                        func.sum(subquery.c.GAMESAGAINST).label("GAMESAGAINST"),
                        (func.sum(subquery.c.GAMESFAVOR) - func.sum(subquery.c.GAMESAGAINST)).label("GAMESDIFFERENCE"),
                        (
                            ((func.sum(subquery.c.POINTS) + func.sum(subquery.c.GAMES) / 3) * 100000) +
                            (func.sum(subquery.c.WINS) *10000) +
                            (func.sum(subquery.c.GAMES) *1000) +
                            ((func.sum(subquery.c.GAMESFAVOR)- func.sum(subquery.c.GAMESAGAINST))*100) +
                            # ((func.sum(subquery.c.WINS) / func.sum(subquery.c.GAMES)) * 10000) +
                            # ((func.sum(subquery.c.GAMESFAVOR) / (func.sum(subquery.c.GAMESFAVOR) + func.sum(subquery.c.GAMESAGAINST))) * 100) +
                            (player_age / 100)
                        ).label("RANKING")
                    )
                    .select_from(subquery)
                    .group_by("GAMEDAYID", "PLAYERID", "PLAYERNAME")
                )
                #print(f"query: {query}")
                result = query.all()
                #print(f"result: {result}")

                for r2 in result:
                    #print(r2)
                    # Write Classification
                    classification = GameDayClassification(
                        gc_idLeague=leagueID,
                        gc_idGameDay=gameDayID,
                        gc_idPlayer=r2.PLAYERID,
                        gc_namePlayer=r2.PLAYERNAME,
                        gc_points=r2.POINTS or 0,
                        gc_wins=r2.WINS or 0,
                        gc_losses=r2.LOSSES or 0,
                        gc_gamesFavor=r2.GAMESFAVOR or 0,
                        gc_gamesAgainst=r2.GAMESAGAINST or 0,
                        gc_gamesDiff=r2.GAMESDIFFERENCE or 0,
                        gc_ranking=r2.RANKING or 0,
                    )
                    db.session.add(classification)

                # Commit the changes to the database
                db.session.commit()

            else:
                # Calculation for players without games
                # Write Classification
                classification = GameDayClassification(
                    gc_idLeague=leagueID,
                    gc_idGameDay=gameDayID,
                    gc_idPlayer=id_player,
                    gc_namePlayer=player_name,
                    gc_points=0,
                    gc_wins=0,
                    gc_losses=0,
                    gc_gamesFavor=0,
                    gc_gamesAgainst=0,
                    gc_gamesDiff=0,
                    gc_ranking=0+(player_age/100),
                )
                db.session.add(classification)
                db.session.commit()

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user

    #print("Reached Finally")
    # Finally we need to update the winners
    winners_query = (
        db.session.query(
            GameDayClassification.gc_idPlayer.label('idPlayer'),
            GameDayClassification.gc_namePlayer.label('namePlayer')
        )
        .filter(GameDayClassification.gc_idLeague == leagueID)
        .filter(GameDayClassification.gc_idGameDay == gameDayID)
        .order_by(GameDayClassification.gc_ranking.desc())
        .limit(2)
        .subquery()
    )

    # Fetch the first winner
    winner1 = (
        db.session.query(winners_query.c.idPlayer, winners_query.c.namePlayer)
        .order_by(winners_query.c.idPlayer.asc())
        .first()
    )

    # Fetch the second winner
    winner2 = (
        db.session.query(winners_query.c.idPlayer, winners_query.c.namePlayer)
        .order_by(winners_query.c.idPlayer.desc())
        .first()
    )

    # Update winners to tb_gameday
    gameday_update_query = (
        db.session.query(GameDay)
        .filter(GameDay.gd_idLeague == leagueID)
        .filter(GameDay.gd_id == gameDayID)
        .update(
            {
                GameDay.gd_idWinner1: winner1.idPlayer,
                GameDay.gd_nameWinner1: winner1.namePlayer,
                GameDay.gd_idWinner2: winner2.idPlayer,
                GameDay.gd_nameWinner2: winner2.namePlayer
            }
        )
    )

    # Commit the changes
    db.session.commit()
    #print("Ended Finally")
    
def calculate_player_age(birthdate):
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age

def func_delete_gameday_players_upd_class(gameDayID):
    gameDay_data = GameDay.query.filter_by(gd_id=gameDayID).first()
    leagueID = gameDay_data.gd_idLeague
    # DONE - Add logic for deleting game day players
    try:
        # Delete games associated with the game day
        Game.query.filter_by(gm_idGameDay=gameDayID).delete()
        # Delete game day players associated with the game day
        GameDayPlayer.query.filter_by(gp_idGameDay=gameDayID).delete()

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        print(f"Error: {e}")
        # Handle the error, maybe log it or display a message to the user

    #Calculate the league classification after
    calculateLeagueClassification(leagueID)
    
def func_create_games_for_gameday(gameDayID):
    #CHECK IF IN tb_game there are already all the games necessary
    GameD = GameDay.query.filter_by(gd_id=gameDayID).first()
    league = League.query.filter_by(lg_id=GameD.gd_idLeague).first()
    league_nbrTeams= league.lg_nbrTeams
    startTime = league.lg_startTime
    league_minWarmUp = league.lg_minWarmUp
    league_minPerGame = league.lg_minPerGame
    league_minBetweenGames = league.lg_minBetweenGames
    leagueId = league.lg_id
    gameDay_Day = GameD.gd_date

    if league_nbrTeams == 2:
        necessary_games = 1
    elif league_nbrTeams == 3:
        necessary_games = 3
    elif league_nbrTeams == 4:
        necessary_games = 6
    elif league_nbrTeams == 5:
        necessary_games = 10
    elif league_nbrTeams == 6:
        necessary_games = 15
    elif league_nbrTeams == 7:
        necessary_games = 21
    elif league_nbrTeams == 8:
        necessary_games = 28
    else:
        necessary_games = 0

    # $gameStart = date('H:i:s', strtotime("+".$league_minWarmUp." minutes", strtotime($startTime)));
    # $gameEnd = date('H:i:s', strtotime("+".$league_minPerGame." minutes", strtotime($gameStart)));
    # Assuming you have startTime as a datetime object, league_minWarmUp, and league_minPerGame as integers
    strTime = datetime.strptime(str(startTime), "%H:%M:%S")  # Convert startTime to datetime if needed

    # Add league_minWarmUp minutes to startTime
    gameStart = strTime + timedelta(minutes=league_minWarmUp)

    # Add league_minPerGame minutes to gameStart
    gameEnd = gameStart + timedelta(minutes=league_minPerGame)

    # Convert gameStart and gameEnd to string format 'H:i:s'
    gameStart_str = gameStart.strftime("%H:%M:%S")
    gameEnd_str = gameEnd.strftime("%H:%M:%S")  
    gameDay_Day_str = gameDay_Day.strftime("%Y-%m-%d")
    #print(gameDay_Day_str)                                      
    # if there are games but the number of games is not the same as the necessary delete all the games
    num_games = Game.query.filter_by(gm_idGameDay=gameDayID).count()
    if num_games != necessary_games:
        Game.query.filter_by(gm_idGameDay=gameDayID).delete()
        # Commit the changes to the database
        db.session.commit()
        num_games = 0

    # if there aren't any games or if they were deleted in the last step create all the necessary games
    if num_games == 0:
        if league_nbrTeams == 2:
            necessary_games = 1
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
        
        elif league_nbrTeams == 3:
            necessary_games = 3
            # Game 1
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 2
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 3
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'C', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
        
        elif league_nbrTeams == 4:
            necessary_games = 6
            # Game 1 and 2
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'C', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 3 and 4
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'B', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 5 and 6
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()

        elif league_nbrTeams == 5:
            necessary_games = 10
            # Game 1 and 2
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 3 and 4
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'C', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'D', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 5 and 6
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'E', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'A', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 7 and 8
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'B', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'C', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 9 and 10
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'D', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'E', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
        
        elif league_nbrTeams == 6:
            necessary_games = 15
            # Game 1, 2 and 3 ROUND 1
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'B', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'C', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'D', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 4, 5 and 6 ROUND 2
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'C', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'F', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'B', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 7, 8 and 9 ROUND 3
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'F', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'A', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 10, 11 and 12 ROUND 4
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'D', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'E', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'F', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 13, 14 and 15 ROUND 5
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'E', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'A', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'D', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            
        elif league_nbrTeams == 7:
            necessary_games = 21
            # Game 1, 2 and 3 ROUND 1
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'B', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'C', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 4, 5 and 6 ROUND 2
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'D', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'E', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'F', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 7, 8 and 9 ROUND 3
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'B', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'C', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'D', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 10, 11 and 12 ROUND 4
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'E', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'F', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'G', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # Game 13, 14 and 15 ROUND 5
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'C', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'D', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'E', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 6
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'F', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'G', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'A', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 7
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'G', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'A', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()

        elif league_nbrTeams == 8:
            necessary_games = 28
            # ROUND 1
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'B', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'C', 'H')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'D', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'E', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 2
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'C', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'A', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'H', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'B', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 3
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'F', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'G', 'H')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'D', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'E', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 4
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'G', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'H', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'B', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'F', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 5
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'A', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'D', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'E', 'H')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'F', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 6
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'D', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'H', 'A')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'B', 'G')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'C', 'F')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            # ROUND 7
            gameStart = gameEnd + timedelta(minutes=league_minBetweenGames)
            gameEnd = gameStart + timedelta(minutes=league_minPerGame)
            gameStart_str = gameStart.strftime("%H:%M:%S")
            gameEnd_str = gameEnd.strftime("%H:%M:%S")  
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 1', 0, 0, 'G', 'C')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 2', 0, 0, 'H', 'B')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 3', 0, 0, 'A', 'E')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            db.session.execute(
                text(f"INSERT INTO tb_game (gm_idLeague, gm_idGameDay, gm_date, gm_timeStart, gm_timeEnd, gm_court, gm_result_A, gm_result_B, gm_teamA, gm_teamB) VALUES (:league_id, :gameDay_id, :gameday_day, :gameStart, :gameEnd, 'Campo 4', 0, 0, 'F', 'D')"),
                {"league_id": leagueId, "gameDay_id": gameDayID, "gameday_day": gameDay_Day_str, "gameStart": gameStart_str, "gameEnd": gameEnd_str}
            )
            db.session.commit()
            
        else:
            necessary_games = 0

def calculate_ELO_full():
    #print("Print from beggining of ELO calc")
    # Delete all rows from tb_ELO_ranking
    try:
        db.session.execute(
            text(f"DELETE FROM tb_ELO_ranking")
        )
        db.session.commit()             
    except Exception as e:
        print("Error1:", e)

    # Delete all rows from tb_ELO_ranking_hist
    try:
        db.session.execute(
            text(f"DELETE FROM tb_ELO_ranking_hist")
        )
        db.session.commit()
    except Exception as e:
        print("Error1:", e)

    # Write every player with 1000 points and 0 games
    try:
        # Execute a SELECT query to fetch the required data from tb_players
        players_data = db.session.execute(
            text("SELECT pl_id, pl_name FROM tb_players")
        ).fetchall()

        # Extract the fetched data and construct the INSERT query
        insert_query = """
            INSERT INTO tb_ELO_ranking (pl_id, pl_name, pl_rankingNow, pl_totalRankingOpo, pl_wins, pl_losses, pl_totalGames)
            VALUES (:pl_id, :pl_name, 1000, 0, 0, 0, 0)
        """

        # Execute the INSERT query for each row of data fetched
        for player in players_data:
            db.session.execute(
                text(insert_query),
                {
                    "pl_id": player[0],
                    "pl_name": player[1]
                }
            )

        # Commit the transaction
        db.session.commit()
    except Exception as e:
        print("Error2:", e)

    # Select every game if league as K higher than 0
    try:
        r1 = db.session.execute(
            text(f"SELECT gm_id, gm_idPlayer_A1, gm_namePlayer_A1, gm_idPlayer_A2, gm_namePlayer_A2, gm_idPlayer_B1, gm_namePlayer_B1, gm_idPlayer_B2, gm_namePlayer_B2, gm_result_A, gm_result_B, gm_idLeague, gm_date, gm_timeStart, gm_idGameDay FROM tb_game WHERE gm_idLeague IN ( SELECT lg_id FROM tb_league WHERE lg_eloK > 0 AND lg_startDate >= :start_date ) AND gm_idPlayer_A1 IS NOT NULL ORDER BY gm_date ASC, gm_timeStart ASC"),
            {"start_date": datetime(2020, 1, 1)},
        ).fetchall()
        

        for d1 in r1:
            # Get current ranking for A1
            A1_ID = d1[1]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': A1_ID}).fetchone()
            A1_ranking = playerInfo[0]
            
            # Get current ranking for A2
            A2_ID = d1[3]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': A2_ID}).fetchone()
            A2_ranking = playerInfo[0]
            
            # Get current ranking for B1
            B1_ID = d1[5]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': B1_ID}).fetchone()
            B1_ranking = playerInfo[0]
            
            # Get current ranking for B2
            B2_ID = d1[7]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': B2_ID}).fetchone()
            B2_ranking = playerInfo[0]

            # Calculate current ELO from teamA and teamB
            ranking_TeamA = (A1_ranking + A2_ranking) / 2
            ranking_TeamB = (B1_ranking + B2_ranking) / 2

            ELO_idLeague = d1[11]
            ELO_idGameDay = d1[14]
            leagueInfo = db.session.execute(text(f"SELECT lg_eloK, lg_id_tp FROM tb_league WHERE lg_id=:league_id"), {'league_id': ELO_idLeague}).fetchone()
            if leagueInfo[1] != 6:
                ELO_K = leagueInfo[0]
            else:
                gameDayInfo = db.session.execute(text(f"(count(*)/2)*10 as lg_eloK FROM tb_gameDayPlayer WHERE gp_idLeague=:league_id and gp_idGameDay=:gameDay_id"), {'league_id': ELO_idLeague, 'gameDay_id': ELO_idGameDay}).fetchone()   
                ELO_K = gameDayInfo[0] 

            # Calculate new ratings
            if d1[9] > d1[10]:
                # Update ratings for team A
                # Calculate rating changes for A1
                delta_A1 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamB - A1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A1, 'player_id': A1_ID})
                # Calculate rating changes for A2
                delta_A2 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamB - A2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A2, 'player_id': A2_ID})
                # Update ratings for team B
                # Calculate rating changes for B1
                delta_B1 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamA - B1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B1, 'player_id': B1_ID})
                # Calculate rating changes for B2
                delta_B2 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamA - B2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B2, 'player_id': B2_ID})
            elif d1[10] > d1[9]:
                # Update ratings for team A
                # Calculate rating changes for A1
                delta_A1 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamB - A1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A1, 'player_id': A1_ID})
                # Calculate rating changes for A2
                delta_A2 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamB - A2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A2, 'player_id': A2_ID})
                # Update ratings for team B
                # Calculate rating changes for B1
                delta_B1 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamA - B1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B1, 'player_id': B1_ID})
                # Calculate rating changes for B2
                delta_B2 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamA - B2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B2, 'player_id': B2_ID})

            if d1[9] == 0 and d1[10] == 0:
                pass
            else:
                # Define the queries
                queries = [
                    {
                        'gm_id': d1[0],
                        'pl_id': A1_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': A2_ID,
                        'op1_id': B1_ID,
                        'op2_id': B2_ID,
                        'result_team': d1[9],
                        'result_op': d1[10],
                        'before_rank': A1_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': A2_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': A1_ID,
                        'op1_id': B1_ID,
                        'op2_id': B2_ID,
                        'result_team': d1[9],
                        'result_op': d1[10],
                        'before_rank': A2_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': B1_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': B2_ID,
                        'op1_id': A1_ID,
                        'op2_id': A2_ID,
                        'result_team': d1[10],
                        'result_op': d1[9],
                        'before_rank': B1_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': B2_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': B1_ID,
                        'op1_id': A1_ID,
                        'op2_id': A2_ID,
                        'result_team': d1[10],
                        'result_op': d1[9],
                        'before_rank': B2_ranking
                    }
                ]
                try:
                    for query in queries:
                        # Convert date strings to Python date objects
                        el_date = datetime.strptime(query['date'], '%Y-%m-%d')
                        el_start_time = datetime.strptime(query['time_start'], '%H:%M:%S').time()
                        # Execute the query
                        db.session.add(
                            ELOrankingHist(
                                el_gm_id=query['gm_id'],
                                el_pl_id=query['pl_id'],
                                el_date=el_date,
                                el_startTime=el_start_time,
                                el_pl_id_teammate=query['teammate_id'],
                                el_pl_name_teammate=db.session.query(Players.pl_name).filter(Players.pl_id == query['teammate_id']).scalar(),
                                el_pl_id_op1=query['op1_id'],
                                el_pl_name_op1=db.session.query(Players.pl_name).filter(Players.pl_id == query['op1_id']).scalar(),
                                el_pl_id_op2=query['op2_id'],
                                el_pl_name_op2=db.session.query(Players.pl_name).filter(Players.pl_id == query['op2_id']).scalar(),
                                el_result_team=query['result_team'],
                                el_result_op=query['result_op'],
                                el_beforeRank=query['before_rank'],
                                el_afterRank=db.session.query(ELOranking.pl_rankingNow).filter(ELOranking.pl_id == query['pl_id']).scalar() or 1000
                            )
                        )
                        db.session.commit()
                    # Commit the transaction
                    db.session.commit()

                except Exception as e:
                    # Rollback the transaction if an error occurs
                    print("Error RHIST:", e)
                    db.session.rollback()

                finally:
                    # Close the session
                    db.session.close()

    except Exception as e:
        print("Error99:", e)

    #print("Print from end of ELO calc")

def calculate_ELO_full_background():
    # Wrap the function you want to execute in the background
    #print("Printing from Background")
    calculate_ELO_full()
    #print("Printing from Background After ELO Calc")

def start_background_task():
    # Start a background thread to execute the task
    #print("Printing before threading")
    background_thread = threading.Thread(target=calculate_ELO_full_background)
    background_thread.start()
    #print("Printing after threading")


def calculate_ELO_parcial():
    # Select every game if league as K higher than 0 and is not on ranking yet
    try:
        r1 = db.session.execute(
            text(f"SELECT gm_id, gm_idPlayer_A1, gm_namePlayer_A1, gm_idPlayer_A2, gm_namePlayer_A2, gm_idPlayer_B1, gm_namePlayer_B1, gm_idPlayer_B2, gm_namePlayer_B2, gm_result_A, gm_result_B, gm_idLeague, gm_date, gm_timeStart, gm_idGameDay FROM tb_game WHERE gm_idLeague IN ( SELECT lg_id FROM tb_league WHERE lg_eloK > 0 AND lg_startDate >= :start_date ) AND gm_id not in (select el_gm_id from tb_ELO_ranking_hist GROUP BY el_gm_id) AND gm_idPlayer_A1 IS NOT NULL ORDER BY gm_date ASC, gm_timeStart ASC"),
            {"start_date": datetime(2020, 1, 1)},
        ).fetchall()
        

        for d1 in r1:
            # Get current ranking for A1
            A1_ID = d1[1]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': A1_ID}).fetchone()
            A1_ranking = playerInfo[0]
            
            # Get current ranking for A2
            A2_ID = d1[3]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': A2_ID}).fetchone()
            A2_ranking = playerInfo[0]
            
            # Get current ranking for B1
            B1_ID = d1[5]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': B1_ID}).fetchone()
            B1_ranking = playerInfo[0]
            
            # Get current ranking for B2
            B2_ID = d1[7]
            playerInfo = db.session.execute(text(f"SELECT pl_rankingNow FROM tb_ELO_ranking WHERE pl_id=:player_id"), {'player_id': B2_ID}).fetchone()
            B2_ranking = playerInfo[0]

            # Calculate current ELO from teamA and teamB
            ranking_TeamA = (A1_ranking + A2_ranking) / 2
            ranking_TeamB = (B1_ranking + B2_ranking) / 2

            ELO_idLeague = d1[11]
            ELO_idGameDay = d1[14]
            leagueInfo = db.session.execute(text(f"SELECT lg_eloK, lg_id_tp FROM tb_league WHERE lg_id=:league_id"), {'league_id': ELO_idLeague}).fetchone()
            if leagueInfo[1] != 6:
                ELO_K = leagueInfo[0]
            else:
                gameDayInfo = db.session.execute(text(f"(count(*)/2)*10 as lg_eloK FROM tb_gameDayPlayer WHERE gp_idLeague=:league_id and gp_idGameDay=:gameDay_id"), {'league_id': ELO_idLeague, 'gameDay_id': ELO_idGameDay}).fetchone()   
                ELO_K = gameDayInfo[0] 

            # Calculate new ratings
            if d1[9] > d1[10]:
                # Update ratings for team A
                # Calculate rating changes for A1
                delta_A1 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamB - A1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A1, 'player_id': A1_ID})
                # Calculate rating changes for A2
                delta_A2 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamB - A2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A2, 'player_id': A2_ID})
                # Update ratings for team B
                # Calculate rating changes for B1
                delta_B1 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamA - B1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B1, 'player_id': B1_ID})
                # Calculate rating changes for B2
                delta_B2 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamA - B2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B2, 'player_id': B2_ID})
            elif d1[10] > d1[9]:
                # Update ratings for team A
                # Calculate rating changes for A1
                delta_A1 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamB - A1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A1, 'player_id': A1_ID})
                # Calculate rating changes for A2
                delta_A2 = ELO_K * (0 - (1 / (1 + 10 ** ((ranking_TeamB - A2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_losses = pl_losses + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_A2, 'player_id': A2_ID})
                # Update ratings for team B
                # Calculate rating changes for B1
                delta_B1 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamA - B1_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B1, 'player_id': B1_ID})
                # Calculate rating changes for B2
                delta_B2 = ELO_K * (1 - (1 / (1 + 10 ** ((ranking_TeamA - B2_ranking) / 400))))
                db.session.execute(text(f"UPDATE tb_ELO_ranking SET pl_rankingNow = pl_rankingNow + :delta, pl_wins = pl_wins + 1, pl_totalGames = pl_totalGames + 1 WHERE pl_id = :player_id"), {'delta': delta_B2, 'player_id': B2_ID})

            if d1[9] == 0 and d1[10] == 0:
                pass
            else:
                # Define the queries
                queries = [
                    {
                        'gm_id': d1[0],
                        'pl_id': A1_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': A2_ID,
                        'op1_id': B1_ID,
                        'op2_id': B2_ID,
                        'result_team': d1[9],
                        'result_op': d1[10],
                        'before_rank': A1_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': A2_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': A1_ID,
                        'op1_id': B1_ID,
                        'op2_id': B2_ID,
                        'result_team': d1[9],
                        'result_op': d1[10],
                        'before_rank': A2_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': B1_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': B2_ID,
                        'op1_id': A1_ID,
                        'op2_id': A2_ID,
                        'result_team': d1[10],
                        'result_op': d1[9],
                        'before_rank': B1_ranking
                    },
                    {
                        'gm_id': d1[0],
                        'pl_id': B2_ID,
                        'date': d1[12],
                        'time_start': d1[13],
                        'teammate_id': B1_ID,
                        'op1_id': A1_ID,
                        'op2_id': A2_ID,
                        'result_team': d1[10],
                        'result_op': d1[9],
                        'before_rank': B2_ranking
                    }
                ]
                try:
                    for query in queries:
                        # Convert date strings to Python date objects
                        el_date = datetime.strptime(query['date'], '%Y-%m-%d')
                        el_start_time = datetime.strptime(query['time_start'], '%H:%M:%S').time()
                        # Execute the query
                        db.session.add(
                            ELOrankingHist(
                                el_gm_id=query['gm_id'],
                                el_pl_id=query['pl_id'],
                                el_date=el_date,
                                el_startTime=el_start_time,
                                el_pl_id_teammate=query['teammate_id'],
                                el_pl_name_teammate=db.session.query(Players.pl_name).filter(Players.pl_id == query['teammate_id']).scalar(),
                                el_pl_id_op1=query['op1_id'],
                                el_pl_name_op1=db.session.query(Players.pl_name).filter(Players.pl_id == query['op1_id']).scalar(),
                                el_pl_id_op2=query['op2_id'],
                                el_pl_name_op2=db.session.query(Players.pl_name).filter(Players.pl_id == query['op2_id']).scalar(),
                                el_result_team=query['result_team'],
                                el_result_op=query['result_op'],
                                el_beforeRank=query['before_rank'],
                                el_afterRank=db.session.query(ELOranking.pl_rankingNow).filter(ELOranking.pl_id == query['pl_id']).scalar() or 1000
                            )
                        )
                        db.session.commit()
                    # Commit the transaction
                    db.session.commit()

                except Exception as e:
                    # Rollback the transaction if an error occurs
                    print("Error RHIST:", e)
                    db.session.rollback()

                finally:
                    # Close the session
                    db.session.close()

    except Exception as e:
        print("Error99:", e)

    #print("Print from end of ELO calc")