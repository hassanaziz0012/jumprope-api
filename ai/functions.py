from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models.workout import Workout
from models.goal import Goal
from models.rest_day import RestDay
from models.chart import Chart
from typing import Dict, Any, List

def get_db_session() -> Session:
    return SessionLocal()

def get_workouts(user_sync_token: str, date_from: str, date_to: str) -> Dict[str, Any]:
    db = get_db_session()
    try:
        from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        workouts = db.query(Workout).filter(
            Workout.user_sync_token == user_sync_token,
            func.date(Workout.date) >= from_dt.date(),
            func.date(Workout.date) <= to_dt.date()
        ).all()
        
        result = [
            {
                "id": w.id,
                "date": w.date.isoformat() if w.date else None,
                "duration": w.duration,
                "total_skips": w.total_skips,
            } for w in workouts
        ]
        return {"workouts": result}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

def get_workout_details(user_sync_token: str, workout_id: str) -> Dict[str, Any]:
    db = get_db_session()
    try:
        workout = db.query(Workout).filter(Workout.id == int(workout_id), Workout.user_sync_token == user_sync_token).first()
        if workout:
            return {
                "id": workout.id,
                "date": workout.date.isoformat() if workout.date else None,
                "duration": workout.duration,
                "total_skips": workout.total_skips,
                "avg_skips_per_minute": workout.avg_skips_per_minute,
                "trips": workout.trips,
                "calories": workout.calories,
                "heart_rate_avg": workout.heart_rate_avg,
                "heart_rate_max": workout.heart_rate_max,
                "notes": workout.notes
            }
        return {"error": "Workout not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

def get_streaks(user_sync_token: str) -> Dict[str, Any]:
    db = get_db_session()
    try:
        workouts = db.query(Workout.date).filter(Workout.user_sync_token == user_sync_token).order_by(Workout.date.asc()).all()
        rest_days = db.query(RestDay.date).filter(RestDay.user_sync_token == user_sync_token).all()
        
        workout_dates = sorted(list(set([w[0].date() for w in workouts if w[0]])))
        rest_dates_set = set()
        for r in rest_days:
            try:
                # Rest dates in DB are typically string "YYYY-MM-DD"
                rest_dates_set.add(datetime.strptime(r[0][:10], "%Y-%m-%d").date())
            except:
                pass
                
        current_streak = 0
        best_streak = 0
        
        if not workout_dates:
            return {
                "current_streak": 0,
                "best_streak": 0,
                "rest_days": [r[0] for r in rest_days]
            }

        dates = workout_dates
        best_streak = 1
        current_temp_streak = 1
        
        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            if diff == 1:
                current_temp_streak += 1
            elif diff > 1:
                # Missing days must be covered by rest days
                all_rest = True
                for d in range(1, diff):
                    if (dates[i-1] + timedelta(days=d)) not in rest_dates_set:
                        all_rest = False
                        break
                if all_rest:
                    pass # streak carries over
                else:
                    current_temp_streak = 1
                    
            best_streak = max(best_streak, current_temp_streak)
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if dates[-1] == today or dates[-1] == yesterday:
            current_streak = current_temp_streak
        else:
            diff = (yesterday - dates[-1]).days
            all_rest = True
            for d in range(1, diff + 1):
                if (dates[-1] + timedelta(days=d)) not in rest_dates_set:
                    all_rest = False
                    break
            if all_rest:
                current_streak = current_temp_streak
            else:
                current_streak = 0
                
        return {
            "current_streak": current_streak,
            "best_streak": best_streak,
            "rest_days": [r[0] for r in rest_days]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

def get_goals(user_sync_token: str) -> Dict[str, Any]:
    db = get_db_session()
    try:
        goals = db.query(Goal).filter(Goal.user_sync_token == user_sync_token).all()
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        workouts_today = db.query(Workout).filter(Workout.user_sync_token == user_sync_token, func.date(Workout.date) == today).all()
        workouts_week = db.query(Workout).filter(Workout.user_sync_token == user_sync_token, func.date(Workout.date) >= start_of_week).all()
        
        skips_today = sum(w.total_skips for w in workouts_today)
        skips_week = sum(w.total_skips for w in workouts_week)
        calories_today = sum(w.calories or 0 for w in workouts_today)
        calories_week = sum(w.calories or 0 for w in workouts_week)
        duration_week = sum(w.duration for w in workouts_week)
        workouts_count_week = len(workouts_week)
        
        result = []
        for g in goals:
            g_data = {"id": g.id}
            
            def calculate_progress(target, current):
                if not target: return 0
                return min(100, int((current / target) * 100))
                
            if g.daily_skips is not None:
                g_data["daily_skips"] = {"target": g.daily_skips, "current": skips_today, "progress_percentage": calculate_progress(g.daily_skips, skips_today)}
            if g.weekly_skips is not None:
                g_data["weekly_skips"] = {"target": g.weekly_skips, "current": skips_week, "progress_percentage": calculate_progress(g.weekly_skips, skips_week)}
            if g.weekly_workouts is not None:
                g_data["weekly_workouts"] = {"target": g.weekly_workouts, "current": workouts_count_week, "progress_percentage": calculate_progress(g.weekly_workouts, workouts_count_week)}
            if g.daily_calories is not None:
                g_data["daily_calories"] = {"target": g.daily_calories, "current": calories_today, "progress_percentage": calculate_progress(g.daily_calories, calories_today)}
            if g.weekly_calories is not None:
                g_data["weekly_calories"] = {"target": g.weekly_calories, "current": calories_week, "progress_percentage": calculate_progress(g.weekly_calories, calories_week)}
            if g.weekly_duration is not None:
                g_data["weekly_duration"] = {"target": g.weekly_duration, "current": duration_week, "progress_percentage": calculate_progress(g.weekly_duration, duration_week)}
            if g.skip_rate_goal is not None:
                avg_rate = (skips_today / len(workouts_today)) if len(workouts_today) > 0 else 0
                g_data["skip_rate_goal"] = {"target": g.skip_rate_goal, "current": avg_rate, "progress_percentage": calculate_progress(g.skip_rate_goal, avg_rate)}
                
            result.append(g_data)

        return {"goals": result}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

def get_chart_data(user_sync_token: str, metric: str, chart_type: str, time_range: str) -> Dict[str, Any]:
    db = get_db_session()
    try:
        days = int(time_range.replace('d', '')) if time_range.endswith('d') else 7
        start_date = date.today() - timedelta(days=days)
        
        workouts = db.query(Workout).filter(Workout.user_sync_token == user_sync_token, func.date(Workout.date) >= start_date).order_by(Workout.date.asc()).all()
        
        data_points = []
        for w in workouts:
            val = 0
            if metric == "totalSkips":
                val = w.total_skips
            elif metric == "avgSkipsPerMin":
                val = w.avg_skips_per_minute or 0
            elif metric == "calories":
                val = w.calories or 0
            elif metric == "trips":
                val = w.trips
                
            data_points.append({
                "date": w.date.isoformat() if w.date else None,
                "value": val
            })
            
        return {
            "metric": metric,
            "chart_type": chart_type,
            "time_range": time_range,
            "data": data_points
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

def create_workout(
    user_sync_token: str,
    duration: int,
    total_skips: int,
    date: str = None,
    avg_skips_per_minute: float = None,
    trips: int = 0,
    calories: float = None,
    heart_rate_avg: int = None,
    heart_rate_max: int = None,
    notes: str = None
) -> Dict[str, Any]:
    try:
        if date:
            dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
            
        return {
            "user_sync_token": user_sync_token,
            "date": dt.isoformat(),
            "duration": duration,
            "total_skips": total_skips,
            "avg_skips_per_minute": avg_skips_per_minute,
            "trips": trips,
            "calories": calories,
            "heart_rate_avg": heart_rate_avg,
            "heart_rate_max": heart_rate_max,
            "notes": notes
        }
    except Exception as e:
        return {"error": str(e)}

def mark_rest_day(user_sync_token: str, date: str) -> Dict[str, Any]:
    try:
        return {
            "user_sync_token": user_sync_token,
            "date": date
        }
    except Exception as e:
        return {"error": str(e)}

def set_goal(user_sync_token: str, name: str, value: float) -> Dict[str, Any]:
    try:
        valid_goals = [
            "daily_skips", "weekly_skips", "weekly_workouts", 
            "daily_calories", "weekly_calories", "weekly_duration", 
            "skip_rate_goal"
        ]
        
        if name not in valid_goals:
            return {"error": f"Invalid goal name. Must be one of: {', '.join(valid_goals)}"}
            
        return {
            "user_sync_token": user_sync_token,
            "updated_goal": name,
            "new_value": value
        }
    except Exception as e:
        return {"error": str(e)}
