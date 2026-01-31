# from geoexpress.core.encoder import encode


# def batch_encode(jobs: list[dict], progress_cb=None):
#     total = len(jobs)
#     results = []

#     for i, job in enumerate(jobs, start=1):
#         if progress_cb:
#             progress_cb(i, total, job)

#         try:
#             out = encode(
#                 job["input"],
#                 job["output"],
#                 job.get("options")
#             )
#             results.append({"job": job, "status": "success", "output": out})
#         except Exception as e:
#             results.append({"job": job, "status": "failed", "error": str(e)})

#     return results

# geoexpress/batch.py

from geoexpress.core.encoder import encode


def batch_encode(jobs: list[dict], progress_cb=None):
    results = []

    for job in jobs:
        try:
            out = encode(
                input=job["input"],
                output=job["output"],
                options=job.get("options"),
                format=job.get("format"),
                password=job.get("password")
            )
            results.append({"job": job, "status": "success", "output": out})
        except Exception as e:
            results.append({"job": job, "status": "failed", "error": str(e)})

    return results
