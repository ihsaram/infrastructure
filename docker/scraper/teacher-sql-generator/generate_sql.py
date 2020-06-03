#!/usr/bin/env python3

import os
import sys
import json
from base64 import b64decode
import psycopg2
from redis import Redis

def enterTeacher(db, teacher):
    school = teacher['school']
    if school:
        teacher['schoolId'] = school['legacyId']
        db.run("INSERT INTO school VALUES (%(legacyId)s, %(name)s, %(state)s, %(city)s) on conflict do nothing", school)
    else:
        teacher['schoolId'] = None

    db.run("""
        INSERT INTO teacher VALUES (
            %(legacyId)s,
            %(firstName)s,
            %(lastName)s,
            (select id from department where name = %(department)s),
            %(schoolId)s
        ) on conflict do nothing
    """, teacher)

    db.run('set time zone UTC')
    for edge in teacher['ratings']['edges']:
        rating = edge['node']
        rating['teacherId'] = teacher['legacyId']
        db.run("""
            INSERT INTO teacher_ratings (
                id,
                admin_review_timestamp,
                is_attendance_mandatory,
                clarity,
                class_name,
                comment,
                is_for_credit,
                timestamp,
                difficulty,
                grade,
                helpful,
                is_online_class,
                tags,
                is_textbook_used,
                helpful_votes,
                not_helpful_votes,
                is_retake_worthy,
                teacher_id
            ) VALUES (
                %(legacyId)s,
                to_timestamp(%(adminReviewedAt)s, 'YYYY-MM-DD hh24:mi:ss'),
                (select (case when %(attendanceMandatory)s is null then null else (case when lower(%(attendanceMandatory)s) like 'y%%' or lower(%(attendanceMandatory)s) = 'mandatory' then 1 else 0 end)::boolean end)),
                %(clarityRating)s,
                %(class)s,
                %(comment)s,
                (select (case when %(courseType)s is null then null else (case when %(courseType)s > 2 then 1 else 0 end)::boolean) end),
                to_timestamp(%(date)s, 'YYYY-MM-DD hh24:mi:ss'),
                %(difficultyRating)s,
                %(grade)s,
                %(helpfulRating)s,
                %(isForOnlineClass)s,
                %(ratingTags)s,
                (select (case when %(textbookUse)s is null then null else (case when %(textbookUse)s > 2 then 1 else 0 end)::boolean) end),
                %(thumbsUpTotal)s,
                %(thumbsDownTotal)s,
                %(wouldTakeAgain)s::boolean,
                %(teacherId)s
            ) on conflict do nothing
        """, rating)


class FileDB:
    def __init__(self):
        self.query = ''
    def mogrify(self, query, params):
        if isinstance(params, dict):
            params_copy = params.copy()
            for key in params_copy:
                if isinstance(params_copy[key], dict) or isinstance(params_copy[key], list):
                    continue
                params_copy[key] = psycopg2.extensions.adapt(params_copy[key]).getquoted().decode('utf8')
        else:
            params_copy = params
        return query % params_copy
    def run(self, query, params=()):
        if 'comment' in params:
            params['comment'] = params['comment'].replace('\x00', ' ')
        self.query += self.mogrify(query, params) + ';\n'
    def get(self):
        return self.query

if __name__ == '__main__':
    redis_host = os.environ.get('REDIS_HOST') or 'shared-redis'
    redis_port = os.environ.get('REDIS_PORT') or 6379
    db = FileDB()
    redis = Redis(host=redis_host, port=redis_port)
    while True:
        payload = json.loads(redis.brpop(['teacher_ratings'], timeout = 0)[1])['data']['node']
        if not payload:
            continue
        teacherId = payload['legacyId']
        try:
            print('Teacher added: %s' % teacherId, flush=True)
            enterTeacher(db, payload)
            redis.lpush('teacher_rating_sqls', db.get())
        except Exception as e:
            print('Failed adding teacher %s, error is: %s' % (teacherId, str(e)), flush=True)
            redis.lpush('failed_teacher_rating_sqls', db.get())
