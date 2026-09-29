from flask import Flask, render_template, request, redirect, url_for, flash, session
import database as db
from ml_engine import MultiStageLandPredictor

app = Flask(__name__)
app.secret_key = "sih_proactive_governance_platform_token"

db.init_db()
ai_engine = MultiStageLandPredictor()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        if db.create_user_profile(username, password, role):
            flash("User Profile Sealed! Please Log In.", "success")
            return redirect(url_for("login"))
        flash("Registration Denied: Identity exists.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_record = db.verify_user_session(username, password)
        if user_record:
            session["user"] = user_record["username"]
            session["role"] = user_record["role"]
            db.log_security_action(user_record["username"], "ESTABLISH_SESSION_ACCESS", "AUTHENTICATION_GATE")
            flash(f"Access Granted. Role Authenticated: {user_record['role']}", "success")
            return redirect(url_for("dashboard"))
        flash("Access Denied: Invalid Security Tokens.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user" in session:
        db.log_security_action(session["user"], "SECURE_EXIT_LOGOUT", "AUTHENTICATION_GATE")
    session.clear()
    flash("Session Context Terminated Securely.", "info")
    return redirect(url_for("login"))

@app.route("/")
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    query = request.args.get("q", "").strip()
    total_evals = db.fetch_total_count()
    
    if query:
        recent_searches = db.search_project_records(query)
    else:
        recent_searches = db.fetch_all_project_records(limit=10)
        
    return render_template("dashboard.html", total_count=total_evals, searches=recent_searches, search_query=query)

@app.route("/projects")
def view_projects():
    if "user" not in session:
        return redirect(url_for("login"))
    
    all_projects = db.fetch_all_project_records(limit=1000)
    return render_template("projects.html", projects=all_projects)

@app.route("/edit_project/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    if "user" not in session:
        return redirect(url_for("login"))
        
    project = db.fetch_project_by_id(project_id)
    if not project:
        flash("Project record not found.", "danger")
        return redirect(url_for("view_projects"))
        
    if request.method == "POST":
        try:
            payload = {
                "project_name": request.form["project_name"],
                "project_type": request.form["project_type"],
                "district": request.form["district"],
                "state": request.form["state"],
                "land_area_hectares": float(request.form["land_area_hectares"]),
                "affected_families_count": int(request.form["affected_families_count"]),
                "compensation_disbursed_pct": float(request.form["compensation_disbursed_pct"]),
                "pending_approvals_days": int(request.form["pending_approvals_days"]),
                "legal_disputes_count": int(request.form["legal_disputes_count"]),
                "possession_status_pct": float(request.form["possession_status_pct"]),
                "rehabilitation_progress_pct": float(request.form["rehabilitation_progress_pct"]),
                "stakeholder_responsiveness_score": float(request.form["stakeholder_responsiveness_score"]),
                "historical_admin_performance": float(request.form["historical_admin_performance"]),
                "documentation_incomplete_pct": float(request.form["documentation_incomplete_pct"])
            }
            
            feature_vector = [
                payload["land_area_hectares"], payload["affected_families_count"], payload["compensation_disbursed_pct"],
                payload["pending_approvals_days"], payload["legal_disputes_count"], payload["possession_status_pct"],
                payload["rehabilitation_progress_pct"], payload["stakeholder_responsiveness_score"],
                payload["historical_admin_performance"], payload["documentation_incomplete_pct"]
            ]
            
            ai_output = ai_engine.calculate_comprehensive_risk(feature_vector)
            
            payload["risk_score"] = ai_output["overall_score"]
            payload["risk_category"] = ai_output["category"]
            payload["sec4_prob"] = ai_output["stage_4_prob"]
            payload["sec11_prob"] = ai_output["stage_11_prob"]
            payload["sec23_prob"] = ai_output["stage_23_prob"]
            payload["primary_driver"] = ai_output["primary_bottleneck"]
            
            db.update_analytical_project(project_id, payload)
            db.log_security_action(session["user"], "UPDATE_PROJECT_ANALYTICS", payload["project_name"])
            
            session["last_recommendations"] = ai_output["action_plans"]
            session["last_project_name"] = payload["project_name"]
            
            flash(f"Project '{payload['project_name']}' updated and re-evaluated successfully!", "success")
            return redirect(url_for("view_projects"))
            
        except Exception as e:
            flash(f"Data Schema Conflict: {str(e)}", "danger")

    return render_template("edit_project.html", project=project)

@app.route("/delete_project/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    project = db.fetch_project_by_id(project_id)
    if project:
        db.delete_analytical_project(project_id)
        db.log_security_action(session["user"], "DELETE_PROJECT_RECORD", project["project_name"])
        flash(f"Project '{project['project_name']}' deleted successfully.", "info")
    else:
        flash("Target project record not found.", "danger")
        
    return redirect(url_for("view_projects"))

@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if "user" not in session:
        return redirect(url_for("login"))
        
    if request.method == "POST":
        try:
            payload = {
                "project_name": request.form["project_name"],
                "project_type": request.form["project_type"],
                "district": request.form["district"],
                "state": request.form["state"],
                "land_area_hectares": float(request.form["land_area_hectares"]),
                "affected_families_count": int(request.form["affected_families_count"]),
                "compensation_disbursed_pct": float(request.form["compensation_disbursed_pct"]),
                "pending_approvals_days": int(request.form["pending_approvals_days"]),
                "legal_disputes_count": int(request.form["legal_disputes_count"]),
                "possession_status_pct": float(request.form["possession_status_pct"]),
                "rehabilitation_progress_pct": float(request.form["rehabilitation_progress_pct"]),
                "stakeholder_responsiveness_score": float(request.form["stakeholder_responsiveness_score"]),
                "historical_admin_performance": float(request.form["historical_admin_performance"]),
                "documentation_incomplete_pct": float(request.form["documentation_incomplete_pct"])
            }
            
            feature_vector = [
                payload["land_area_hectares"], payload["affected_families_count"], payload["compensation_disbursed_pct"],
                payload["pending_approvals_days"], payload["legal_disputes_count"], payload["possession_status_pct"],
                payload["rehabilitation_progress_pct"], payload["stakeholder_responsiveness_score"],
                payload["historical_admin_performance"], payload["documentation_incomplete_pct"]
            ]
            
            ai_output = ai_engine.calculate_comprehensive_risk(feature_vector)
            
            payload["risk_score"] = ai_output["overall_score"]
            payload["risk_category"] = ai_output["category"]
            payload["sec4_prob"] = ai_output["stage_4_prob"]
            payload["sec11_prob"] = ai_output["stage_11_prob"]
            payload["sec23_prob"] = ai_output["stage_23_prob"]
            payload["primary_driver"] = ai_output["primary_bottleneck"]
            
            db.save_analytical_project(payload)
            db.log_security_action(session["user"], "RUN_PREDICTIVE_INFERENCE", payload["project_name"])
            
            session["last_recommendations"] = ai_output["action_plans"]
            session["last_project_name"] = payload["project_name"]
            
            flash("AI Scoring Evaluation Completed Successfully!", "success")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            flash(f"Data Schema Conflict: {str(e)}", "danger")
            
    return render_template("analyze.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)