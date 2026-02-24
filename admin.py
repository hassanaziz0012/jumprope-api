from sqladmin import ModelView
from models.workout import Workout
from models.goal import Goal
from models.chart import Chart
from models.user_profile import UserProfile
from models.rest_day import RestDay
from models.conversation import Conversation, ConversationMessage

class WorkoutAdmin(ModelView, model=Workout):
    column_list = [Workout.id, Workout.date, Workout.duration, Workout.total_skips]

class GoalAdmin(ModelView, model=Goal):
    column_list = [Goal.id, Goal.daily_skips, Goal.weekly_skips, Goal.weekly_workouts]

class ChartAdmin(ModelView, model=Chart):
    column_list = [Chart.id, Chart.metric, Chart.time_range, Chart.type]

class UserProfileAdmin(ModelView, model=UserProfile):
    column_list = [UserProfile.id, UserProfile.name, UserProfile.email, UserProfile.ai_enabled]

class RestDayAdmin(ModelView, model=RestDay):
    column_list = [RestDay.id, RestDay.date, RestDay.created_at]

class ConversationAdmin(ModelView, model=Conversation):
    column_list = [Conversation.id, Conversation.title, Conversation.created_at]

class ConversationMessageAdmin(ModelView, model=ConversationMessage):
    column_list = [ConversationMessage.id, ConversationMessage.conversation_id, ConversationMessage.role, ConversationMessage.created_at]
