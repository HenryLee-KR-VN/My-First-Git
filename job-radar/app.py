#!/usr/bin/env python3
"""job-radar 웹 대시보드. 실행: python app.py  (http://localhost:8080)"""
from collections import Counter
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

from db import get_conn, init_db

app = Flask(__name__)


def row_to_dict(row):
    d = dict(row)
    d["tech_stack"] = [t for t in (d.get("tech_stack") or "").split(",") if t]
    return d


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/jobs")
def api_jobs():
    """필터링된 공고 리스트. 정렬: 등록일 최신순."""
    source = request.args.get("source")
    domain = request.args.get("domain")
    employment_type = request.args.get("employment_type")
    career_level = request.args.get("career_level")
    location = request.args.get("location")
    stacks = request.args.getlist("stack")
    q = request.args.get("q", "").strip()

    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if source:
        sql += " AND source = ?"
        params.append(source)
    if domain:
        sql += " AND company_domain = ?"
        params.append(domain)
    if employment_type:
        sql += " AND employment_type = ?"
        params.append(employment_type)
    if career_level:
        sql += " AND career_level = ?"
        params.append(career_level)
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    if q:
        sql += " AND (job_title LIKE ? OR company_name LIKE ? OR tech_stack LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    for s in stacks:
        sql += " AND tech_stack LIKE ?"
        params.append(f"%{s}%")

    sql += " ORDER BY posted_date DESC, id DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/filters")
def api_filters():
    """필터 드롭다운을 채우기 위한 고유값 목록."""
    with get_conn() as conn:
        rows = conn.execute("SELECT source, company_domain, employment_type, career_level, location, tech_stack FROM jobs").fetchall()

    sources, domains, emp_types, careers, locations = set(), set(), set(), set(), set()
    stacks = set()
    for r in rows:
        if r["source"]:
            sources.add(r["source"])
        if r["company_domain"]:
            domains.add(r["company_domain"])
        if r["employment_type"]:
            emp_types.add(r["employment_type"])
        if r["career_level"]:
            careers.add(r["career_level"])
        if r["location"]:
            locations.add(r["location"])
        for s in (r["tech_stack"] or "").split(","):
            if s:
                stacks.add(s)

    return jsonify({
        "sources": sorted(sources),
        "domains": sorted(domains),
        "employment_types": sorted(emp_types),
        "career_levels": sorted(careers),
        "locations": sorted(locations),
        "stacks": sorted(stacks),
    })


def _since_date(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


@app.route("/api/trends")
def api_trends():
    """트렌드 대시보드용 집계 데이터. ?days=7 또는 30"""
    days = request.args.get("days", 7, type=int)
    since = _since_date(days)

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT company_name, company_domain, tech_stack, posted_date FROM jobs WHERE posted_date >= ?",
            (since,),
        ).fetchall()

    domain_counter = Counter()
    stack_counter = Counter()
    company_counter = Counter()
    daily_counter = Counter()

    for r in rows:
        if r["company_domain"]:
            domain_counter[r["company_domain"]] += 1
        if r["company_name"]:
            company_counter[r["company_name"]] += 1
        if r["posted_date"]:
            daily_counter[r["posted_date"]] += 1
        for s in (r["tech_stack"] or "").split(","):
            if s:
                stack_counter[s] += 1

    daily_sorted = sorted(daily_counter.items())

    top_stack = stack_counter.most_common(1)
    top_domain = domain_counter.most_common(1)

    return jsonify({
        "days": days,
        "new_jobs_count": len(rows),
        "top_stack": top_stack[0][0] if top_stack else None,
        "top_domain": top_domain[0][0] if top_domain else None,
        "domain_counts": domain_counter.most_common(),
        "stack_counts_top15": stack_counter.most_common(15),
        "daily_counts": daily_sorted,
        "top_companies": company_counter.most_common(10),
    })


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=True)
