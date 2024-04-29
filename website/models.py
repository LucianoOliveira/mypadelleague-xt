from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class AdminUser(db.Model):
    __tablename__ = 'tb_adminUsers'
    au_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    au_user = db.Column(db.String(50), nullable=False)
    au_psw = db.Column(db.String(150))
    au_status = db.Column(db.Integer, default=None)

class ELOranking(db.Model):
    __tablename__ = 'tb_ELO_ranking'
    pl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pl_name = db.Column(db.String(50), nullable=False)
    pl_rankingNow = db.Column(db.Float)
    pl_totalRankingOpo = db.Column(db.Float)
    pl_wins = db.Column(db.Integer, nullable=False)
    pl_losses = db.Column(db.Integer, nullable=False)
    pl_totalGames = db.Column(db.Integer, nullable=False)

class ELOrankingHist(db.Model):
    __tablename__ = 'tb_ELO_ranking_hist'
    el_gm_id = db.Column(db.Integer, nullable=False, primary_key=True)  # Composite primary key
    el_pl_id = db.Column(db.Integer, nullable=False, primary_key=True)  # Composite primary key
    el_date = db.Column(db.Date)
    el_startTime = db.Column(db.Time)
    el_pl_id_teammate = db.Column(db.Integer, nullable=False)
    el_pl_name_teammate = db.Column(db.String(50), nullable=False)
    el_pl_id_op1 = db.Column(db.Integer, nullable=False)
    el_pl_name_op1 = db.Column(db.String(50), nullable=False)
    el_pl_id_op2 = db.Column(db.Integer, nullable=False)
    el_pl_name_op2 = db.Column(db.String(50), nullable=False)
    el_result_team = db.Column(db.Integer, nullable=False)
    el_result_op = db.Column(db.Integer, nullable=False)
    el_beforeRank = db.Column(db.Float)
    el_afterRank = db.Column(db.Float)

    # Composite primary key constraint
    __table_args__ = (
        db.PrimaryKeyConstraint('el_gm_id', 'el_pl_id'),
    )

    def __repr__(self):
        return f"<ELOrankingHist(el_gm_id={self.el_gm_id}, el_pl_id={self.el_pl_id}, ...)>"

class Game(db.Model):
    __tablename__ = 'tb_game'
    gm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gm_idLeague = db.Column(db.Integer, nullable=False)
    gm_idGameDay = db.Column(db.Integer, nullable=False)
    gm_date = db.Column(db.Date)
    gm_timeStart = db.Column(db.Time)
    gm_timeEnd = db.Column(db.Time)
    gm_court = db.Column(db.String(50))
    gm_idPlayer_A1 = db.Column(db.Integer)
    gm_namePlayer_A1 = db.Column(db.String(50))
    gm_idPlayer_A2 = db.Column(db.Integer)
    gm_namePlayer_A2 = db.Column(db.String(50))
    gm_idPlayer_B1 = db.Column(db.Integer)
    gm_namePlayer_B1 = db.Column(db.String(50))
    gm_idPlayer_B2 = db.Column(db.Integer)
    gm_namePlayer_B2 = db.Column(db.String(50))
    gm_result_A = db.Column(db.Integer)
    gm_result_B = db.Column(db.Integer)
    gm_teamA = db.Column(db.String(1))
    gm_teamB = db.Column(db.String(1))
    gm_type = db.Column(db.String(50))

class GameDay(db.Model):
    __tablename__ = 'tb_gameday'
    gd_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gd_idLeague = db.Column(db.Integer, nullable=False)
    gd_teamNum = db.Column(db.Integer)
    gd_date = db.Column(db.Date)
    gd_status = db.Column(db.String(20), nullable=False)
    gd_idWinner1 = db.Column(db.Integer)
    gd_nameWinner1 = db.Column(db.String(50))
    gd_idWinner2 = db.Column(db.Integer)
    gd_nameWinner2 = db.Column(db.String(50))
    gd_gameDayName = db.Column(db.String(50))

class GameDayClassification(db.Model):
    __tablename__ = 'tb_gameDayClassification'
    gc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gc_idLeague = db.Column(db.Integer, nullable=False)
    gc_idGameDay = db.Column(db.Integer, nullable=False)
    gc_idPlayer = db.Column(db.Integer, nullable=False)
    gc_namePlayer = db.Column(db.String(50), nullable=False)
    gc_points = db.Column(db.Integer, nullable=False)
    gc_wins = db.Column(db.Integer, nullable=False)
    gc_losses = db.Column(db.Integer, nullable=False)
    gc_gamesFavor = db.Column(db.Integer, nullable=False)
    gc_gamesAgainst = db.Column(db.Integer, nullable=False)
    gc_gamesDiff = db.Column(db.Integer, nullable=False)
    gc_ranking = db.Column(db.Float, nullable=False)

class GameDayPlayer(db.Model):
    __tablename__ = 'tb_gameDayPlayer'
    gp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gp_idLeague = db.Column(db.Integer, nullable=False)
    gp_idGameDay = db.Column(db.Integer, nullable=False)
    gp_idPlayer = db.Column(db.Integer, nullable=False)
    gp_namePlayer = db.Column(db.String(50), nullable=False)
    gp_team = db.Column(db.String(1))

class League(db.Model):
    __tablename__ = 'tb_league'
    lg_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lg_name = db.Column(db.String(50))
    lg_level = db.Column(db.String(20))
    lg_status = db.Column(db.String(20))
    lg_nbrDays = db.Column(db.Integer)
    lg_nbrTeams = db.Column(db.Integer)
    lg_startDate = db.Column(db.Date)
    lg_endDate = db.Column(db.Date)
    lg_startTime = db.Column(db.Time)
    lg_minWarmUp = db.Column(db.Integer)
    lg_minPerGame = db.Column(db.Integer)
    lg_minBetweenGames = db.Column(db.Integer)
    lg_typeOfLeague = db.Column(db.String(50))
    tb_maxLevel = db.Column(db.Integer)
    lg_sponsor = db.Column(db.String(50))
    lg_eloK = db.Column(db.Integer)
    lg_zeroSumK = db.Column(db.Integer)
    lg_id_tp = db.Column(db.Integer)

class LeagueClassification(db.Model):
    __tablename__ = 'tb_leagueClassification'
    lc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lc_idLeague = db.Column(db.Integer, nullable=False)
    lc_idPlayer = db.Column(db.Integer, nullable=False)
    lc_namePlayer = db.Column(db.String(50), nullable=False)
    lc_points = db.Column(db.Integer, nullable=False)
    lc_wins = db.Column(db.Integer, nullable=False)
    lc_losses = db.Column(db.Integer, nullable=False)
    lc_gamesFavor = db.Column(db.Integer, nullable=False)
    lc_gamesAgainst = db.Column(db.Integer, nullable=False)
    lc_gamesDiff = db.Column(db.Integer, nullable=False)
    lc_ranking = db.Column(db.Float, nullable=False)

class Players(db.Model, UserMixin):
    __tablename__ = 'tb_players'
    pl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pl_name = db.Column(db.String(50), nullable=False)
    pl_acron = db.Column(db.String(3))
    pl_email = db.Column(db.String(200))
    pl_pwd = db.Column(db.String(150))
    # pl_photo = db.Column(db.Binary)
    pl_birthday = db.Column(db.Date)
    pl_type = db.Column(db.String(5))
    pl_sex = db.Column(db.String(1))
    pl_level_sex = db.Column(db.Integer)
    pl_level_mx = db.Column(db.Integer)
    pl_ranking_stat = db.Column(db.String(1), nullable=False, default='Y')
    def get_id(self):
        return str(self.pl_id)

class RoundRobinTeams(db.Model):
    __tablename__ = 'tb_roundRobinTeams'
    rt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rt_name = db.Column(db.Integer, nullable=False)
    rt_idPlayer1 = db.Column(db.Integer, nullable=False)
    rt_namePlayer1 = db.Column(db.String(100), nullable=False)
    rt_idPlayer2 = db.Column(db.Integer, nullable=False)
    rt_namePlayer2 = db.Column(db.String(100), nullable=False)
    rt_level = db.Column(db.Integer, nullable=False)

