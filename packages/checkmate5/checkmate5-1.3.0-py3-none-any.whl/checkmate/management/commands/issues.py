# -*- coding: utf-8 -*-
from checkmate.lib.models import Issue, IssueOccurrence, Snapshot
from checkmate.contrib.plugins.git.models import GitSnapshot
from checkmate.management.commands.base import BaseCommand
import logging
import json
import os
try:
    from rich.console import Console
    from rich.table import Table
    from rich import print
except Exception:
    Console = None
    Table = None
    print = __builtins__["print"]

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    options = BaseCommand.options + [
        {
            'name': '--raw-sql',
            'action': 'store_true',
            'dest': 'raw_sql',
            'default': False,
            'help': 'print raw sqlite queries and sample rows.',
        }
        ,
        {
            'name': '--snapshots',
            'action': 'store_true',
            'dest': 'snapshots',
            'default': False,
            'help': 'list available snapshots and exit.',
        },
        {
            'name': '--snapshot',
            'action': 'store',
            'dest': 'snapshot',
            'default': None,
            'help': 'filter issues by snapshot id (prefix match).',
        },
        {
            'name': '--html-output',
            'action': 'store_true',
            'dest': 'html_output',
            'default': False,
            'help': 'write HTML report to report.html.',
        },
        {
            'name': '--json-output',
            'action': 'store_true',
            'dest': 'json_output',
            'default': False,
            'help': 'write JSON report to report.json.',
        },
        {
            'name': '--sarif-output',
            'action': 'store_true',
            'dest': 'sarif_output',
            'default': False,
            'help': 'write SARIF report to report.sarif.',
        },
    ]

    """
    Returns a list of issues for the current snapshot or file revision.
    """

    def run(self):
        snapshot_pk = self.opts.get('snapshot')
        filenames = None
        output_html = bool(self.opts.get('html_output'))
        output_json = bool(self.opts.get('json_output'))
        output_sarif = bool(self.opts.get('sarif_output'))

        high = ["SQL", "injection", "unauthorized", "forgery", "overflow", "unescaped", "traversal", "overflow", "boundaries", "eval", "attacks"]
        medium = ["insecurely", "insecure", "exec", "cross-site", "XSS", "unsafe", "redirect", "splitting"]
        
        if self.extra_args:
            # Backward compatibility: `checkmate issues html/json/sarif`
            if self.extra_args[0] == "html":
                output_html = True
            elif self.extra_args[0] == "json":
                output_json = True
            elif self.extra_args[0] == "sarif":
                output_sarif = True

        if self.opts.get('snapshots'):
            snapshots = []
            try:
                snapshots.extend(list(self.backend.filter(GitSnapshot, {})))
            except Exception:
                pass
            try:
                snapshots.extend(list(self.backend.filter(Snapshot, {})))
            except Exception:
                pass
            if not snapshots:
                print("No snapshots found.")
                return 0
            for snap in snapshots:
                snap_id = getattr(snap, 'pk', None)
                snap_time = getattr(snap, 'created_at', None) or getattr(snap, 'committer_date', None)
                print(f"{snap_id}\t{snap_time}")
            return 0

        if self.opts.get('raw_sql'):
            try:
                import sqlite3
                engine = getattr(self.backend, "engine", None) or getattr(self.backend.backend, "engine", None)
                db_path = None
                if engine and engine.url and engine.url.database:
                    db_path = engine.url.database
                if not db_path:
                    logger.error("Unable to resolve sqlite database path.")
                    return -1

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                print(f"sqlite db: {db_path}")
                print("tables:", [r[0] for r in cur.execute("select name from sqlite_master where type='table' order by name").fetchall()])
                print("issue count:", cur.execute("select count(*) from issue").fetchone()[0])
                print("issue sample:")
                for row in cur.execute("select pk, data from issue limit 5").fetchall():
                    print(row)
                conn.close()
                return 0
            except Exception as exc:
                logger.error("Failed to query sqlite database: %s", exc)
                return -1

        snapshot = None
        if snapshot_pk:
            SnapshotClass = GitSnapshot
            try:
                snapshot = self.backend.get(SnapshotClass,
                                            {'pk': {'$regex': r'^'+snapshot_pk}})
                if snapshot is None:
                    raise SnapshotClass.DoesNotExist()
            except SnapshotClass.DoesNotExist:
                from checkmate.lib.models import Snapshot as BaseSnapshot
                try:
                    snapshot = self.backend.get(BaseSnapshot,
                                                {'pk': {'$regex': r'^'+snapshot_pk}})
                    if snapshot is None:
                        raise BaseSnapshot.DoesNotExist()
                except BaseSnapshot.DoesNotExist:
                    logger.warning("Snapshot %s does not exist; showing issues without snapshot filter.", snapshot_pk)
            except SnapshotClass.MultipleDocumentsReturned:
                logger.warning("Ambiguous key %s; showing issues without snapshot filter.", snapshot_pk)
        else:
            # Use the latest snapshot by default if available
            try:
                snap_list = list(self.backend.filter(Snapshot, {}))
                if snap_list:
                    snap_list = sorted(snap_list, key=lambda s: getattr(s, 'created_at', 0), reverse=True)
                    snapshot = snap_list[0]
            except Exception:
                snapshot = None

        issues = self.backend.filter(Issue, {})
        if snapshot is not None:
            try:
                file_revisions = list(snapshot.file_revisions)
                file_revision_ids = []
                for fr in file_revisions:
                    if isinstance(fr, dict):
                        file_revision_ids.append(fr.get('pk'))
                    else:
                        file_revision_ids.append(getattr(fr, 'pk', None))
                file_revision_ids = [fid for fid in file_revision_ids if fid]

                if not file_revision_ids:
                    try:
                        import sqlite3
                        engine = getattr(self.backend, "engine", None) or getattr(self.backend.backend, "engine", None)
                        db_path = None
                        if engine and engine.url and engine.url.database:
                            db_path = engine.url.database
                        if db_path:
                            conn = sqlite3.connect(db_path)
                            cur = conn.cursor()
                            rows = cur.execute(
                                "select filerevision from snapshot_filerevision_file_revisions where snapshot = ?",
                                (snapshot.pk,),
                            ).fetchall()
                            conn.close()
                            file_revision_ids = [r[0] for r in rows if r and r[0]]
                    except Exception:
                        file_revision_ids = []

                if file_revision_ids:
                    occurrences = self.backend.filter(
                        IssueOccurrence,
                        {'file_revision': {'$in': file_revision_ids}},
                        include=('issue', 'file_revision'),
                    )
                    issues = []
                    for occ in occurrences:
                        issue = getattr(occ, 'issue', None)
                        if issue is None:
                            continue
                        issue_dict = issue
                        try:
                            issue_dict['file'] = getattr(occ.file_revision, 'path', issue_dict.get('file'))
                            issue_dict['line'] = occ.get('from_row') or issue_dict.get('line')
                        except Exception:
                            pass
                        issues.append(issue_dict)

                if file_revision_ids and not issues:
                    try:
                        import sqlite3
                        engine = getattr(self.backend, "engine", None) or getattr(self.backend.backend, "engine", None)
                        db_path = None
                        if engine and engine.url and engine.url.database:
                            db_path = engine.url.database
                        if db_path:
                            conn = sqlite3.connect(db_path)
                            cur = conn.cursor()
                            placeholders = ",".join(["?"] * len(file_revision_ids))
                            query = (
                                "select io.from_row, fr.path, i.data "
                                "from issueoccurrence io "
                                "join issue i on i.pk = io.issue "
                                "left join filerevision fr on fr.pk = io.file_revision "
                                f"where io.file_revision in ({placeholders})"
                            )
                            rows = cur.execute(query, file_revision_ids).fetchall()
                            conn.close()
                            for from_row, path, data in rows:
                                try:
                                    issue_dict = json.loads(data)
                                except Exception:
                                    issue_dict = {}
                                if 'file' not in issue_dict and path:
                                    issue_dict['file'] = path
                                if 'line' not in issue_dict and from_row:
                                    issue_dict['line'] = from_row
                                issues.append(issue_dict)
                    except Exception:
                        pass
            except Exception:
                logger.warning("Failed to filter by snapshot; showing all issues.")
        try:
            issues = issues.sort('analyzer', 1)
        except Exception:
            try:
                issues = sorted(list(issues), key=lambda i: i.get('analyzer', ''))
            except Exception:
                issues = list(issues) if issues is not None else []

        if not isinstance(issues, list):
            try:
                issues = list(issues)
            except Exception:
                issues = [] if issues is None else issues

        if not issues:
            try:
                import sqlite3
                engine = getattr(self.backend, "engine", None) or getattr(self.backend.backend, "engine", None)
                db_path = None
                if engine and engine.url and engine.url.database:
                    db_path = engine.url.database
                if db_path:
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    snap_pk = getattr(snapshot, "pk", None)
                    rows = []
                    if snap_pk:
                        snap_rows = cur.execute(
                            "select filerevision from snapshot_filerevision_file_revisions where snapshot = ?",
                            (snap_pk,),
                        ).fetchall()
                        file_revision_ids = [r[0] for r in snap_rows if r and r[0]]
                        if file_revision_ids:
                            placeholders = ",".join(["?"] * len(file_revision_ids))
                            query = (
                                "select io.from_row, fr.path, i.data, i.analyzer "
                                "from issueoccurrence io "
                                "join issue i on i.pk = io.issue "
                                "left join filerevision fr on fr.pk = io.file_revision "
                                f"where io.file_revision in ({placeholders})"
                            )
                            rows = cur.execute(query, file_revision_ids).fetchall()
                    if not rows:
                        rows = cur.execute("select data, analyzer from issue").fetchall()
                    conn.close()
                    issues = []
                    for row in rows:
                        if len(row) == 2:
                            data, analyzer = row
                            path = None
                            from_row = None
                        else:
                            from_row, path, data, analyzer = row
                        try:
                            issue_dict = json.loads(data)
                        except Exception:
                            issue_dict = {}
                        if analyzer and 'analyzer' not in issue_dict:
                            issue_dict['analyzer'] = analyzer
                        if path and 'file' not in issue_dict:
                            issue_dict['file'] = path
                        if from_row and 'line' not in issue_dict:
                            issue_dict['line'] = from_row
                        issues.append(issue_dict)
            except Exception:
                pass

        for issue in issues:
            try:
                if issue.get('analyzer') is None:
                    issue['analyzer'] = getattr(issue, 'analyzer', None)
            except Exception:
                pass

        def _dedupe_issues(items):
            unique = []
            seen = set()
            for issue in items:
                try:
                    line = issue.get("line") if hasattr(issue, "get") else issue["line"]
                    file_path = issue.get("file") if hasattr(issue, "get") else issue["file"]
                except Exception:
                    line = None
                    file_path = None
                if line in (None, 0):
                    line = 1
                    try:
                        issue["line"] = line
                    except Exception:
                        pass
                if not file_path:
                    file_path = "N/A"
                    try:
                        issue["file"] = file_path
                    except Exception:
                        pass
                key = (file_path, line)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(issue)
            return unique

        # License check removed; always show full issue details.
        valid = 1

        if not (output_html or output_json or output_sarif):
          unique = _dedupe_issues(issues)

          if Table is None:
            for issue in unique:
              if issue.get('code') != "AnalysisError":
                severity = issue.get('severity') or "Warning"
                desc_lower = issue['data'].lower()
                if any(ele in desc_lower for ele in high):
                  severity = "High"
                if any(ele in desc_lower for ele in medium):
                  severity = "Medium"
                print(f"{severity}\t{issue.get('analyzer','N/A')}\t{issue.get('file','N/A')}\t{issue.get('line','')}\t{issue['data']}")
            print("Thank you for using Checkmate.")
            return 0

          table = Table(title="Scan Report")
          table.add_column("Description", style="magenta")
          table.add_column("Severity", justify="right", style="green")
          table.add_column("Plugin", justify="right", style="green")
          table.add_column("File", justify="right", style="green")
          table.add_column("Line", justify="right", style="green")
          table.add_column("Status", justify="right", style="green")

          for issue in unique:
            if issue.get('code') != "AnalysisError":
              try:
                severity = issue.get('severity', 'Unknown')
                if issue['severity'] == "High":
                  severity = "[red] High"
                elif issue['severity'] == "Medium":
                  severity = "[yellow] Medium"
              except:
                severity = "Unknown"

              desc = issue.get('data') or issue.get('description') or issue.get('message') or ""
              desc_lower = desc.lower()
              res = [ele for ele in high if(ele in desc_lower)]
              if bool(res) is True:
               severity = "[red] High"
              res = [ele for ele in medium if(ele in desc_lower)]
              if bool(res) is True:
                severity = "[yellow] Medium"
              table.add_row(desc, severity, issue.get('analyzer',"N/A"), issue.get('file',"N/A"), str(issue.get('line',"")), "❌")

          console = Console()
          console.print(table)
          print("Thank you for using Checkmate.") 

          #for issue in issues:
          #    print(("%(analyzer)s\t%(code)s\t" % {'analyzer': issue['analyzer'],
          #                                       'code': issue['code']}))
        else:
          jsonout = []
          out = {}
          unique = _dedupe_issues(issues)



          for issue in unique:
            if issue.get('code') != "AnalysisError":
              out = {}
              try:
                severity = issue.get('severity', 'Unknown')
              except:
                severity = "Unknown"
              desc = issue.get('data') or issue.get('description') or issue.get('message') or ""
              desc_lower = desc.lower()
              res = [ele for ele in high if(ele in desc_lower)]
              if bool(res) is True:
                severity = "High"
              res = [ele for ele in medium if(ele in desc_lower)]
              if bool(res) is True:
                severity = "Medium"
              out['hash'] =  issue.get('hash')
              out['description'] = desc
              out['severity'] = severity
              out['plugin'] = issue.get('analyzer',"N/A")
              out['file'] = issue.get('file',"N/A")
              out['line'] = issue.get('line', "")
              jsonout.append(out)
              out={}
       
   
          head = """
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  <title>Report</title>
  <script type='text/javascript' src='https://code.jquery.com/jquery-2.1.0.js'></script>

  <script type='text/javascript' src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/js/bootstrap.min.js"></script>

  <link href="https://dl.betterscan.io/reportstyle.css" rel="stylesheet">





<script type='text/javascript'>//<![CDATA[
$(window).load(function(){
var data =
"""
          
          json_object = json.dumps(jsonout, indent = 4) 

          end = """
var sort_by = function(field, reverse, primer){

   var key = primer ?
       function(x) {return primer(x[field])} :
       function(x) {return x[field]};

   reverse = !reverse ? 1 : -1;

   return function (a, b) {
       return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
     }
}

for(var i = 0; i < data.length; i++) {

    if(data[i].risk=="Information")
    {
        data[i].risk_no=1;
    }

    if(data[i].risk=="Low")
    {
        data[i].risk_no=2;
    }

    if(data[i].risk=="Medium")
    {
        data[i].risk_no=3;
    }

    if(data[i].risk=="High")
    {
        data[i].risk_no=4;
    }





}

data.sort(sort_by('risk_no', true, parseInt));



for(var i = 0; i < data.length; i++) {
$('#findings').append("<tbody><tr><th>File</th><td>"+data[i].file+"</td></tr>");
$('#findings').append("<tr><th>Description</th><td>"+data[i].description+"</td></tr>");
$('#findings').append("<tr><th>Severity</th><td>"+data[i].severity+"</td></tr>");
$('#findings').append("<tr><th>Plugin</th><td>"+data[i].plugin+"</td></tr>");
$('#findings').append("<tr><th>Line</th><td>"+data[i].line+"</td></tr></tbody></table>");
$('#findings').append("<hr>");

}


});//]]>

</script>


</head>

 <div class="container-fluid">




<p style="margin-bottom: 25px;"><img src="https://dl.betterscan.io/logo.png" style="position:relative; top:-40px;"></p>

<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        <li class="active"><a href="#overview" data-toggle="tab">Summary</a></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane fade in active" id="overview">


<div class="alert alert-info">
    <b>Tags</b>:

        Security Final Report


</div>

<section id="information">
    <div class="box">
        <h4>Report</h4>
        <div class="box-content" style="padding: 0;">
            <table class="table">
                <thead>
                    <tr>
                        <th style="border-top: 0;">Type</th>

                         <td style="border-top: 0;">FILE</td>
                    </tr>
                </thead>
            </table>
        </div>
    </div>


</section>
<hr>

    <section id="file">
    <h4>File Details</h4>
    <div class="box">
        <div class="box-content" style="padding: 0;">
            <table class="table">
                <tbody><tr>
                    <th style="border-top: 0;">File Name</th>
                    <td style="border-top: 0;">report.html</td>
                </tr>
                <tr>
                    <th>File Type</th>
                    <td>data</td>
                </tr>
            </tbody></table>
        </div>
    </div>
</section>



  <div align="center"><h1>Scan Report</h1></div>


<hr>
  <h4>Code</h4>

 <section id="findings1">
    <div class="box">

        <div id="findings" class="box-content" style="padding: 0;">
        </div>
    </div>
</section>

</div>

</body>


</html>


"""
          if output_html:
            f = open("report.html", "w")
            f.write(head)
            f.write(json_object)
            f.write(end)
            f.close()

          if output_json:
            f = open("report.json", "w")
            f.write(json_object)
            f.close()


          rules = {}
          results = []
          i = 0
          for item in jsonout:

                short_description = item['description']
                full_description = (item['description'])
                message = item['description']
                fname = item['file']
                line = item['line']

                try:
                  severity = item['severity']
                except:
                  severity = "Warning"
                desc_lower = item['description'].lower()
                res = [ele for ele in high if(ele in desc_lower)]
                if bool(res) is True:
                  severity = "High"
                res = [ele for ele in medium if(ele in desc_lower)]
                if bool(res) is True:
                  severity = "Medium"
               
                rules[i] = {
                        "id": str(i),
                        "name": "BetterscanRule",
                        # This appears as the title on the list and individual issue view
                        "shortDescription": {"text": short_description},
                        # This appears as a sub heading on the individual issue view
                        "fullDescription": {"text": full_description},
                        # This appears on the individual issue view in an expandable box
                        "helpUri": "https://betterscan.io",
                        "help": {
                            "markdown": item['description'],
                            # This property is not used if markdown is provided, but is required
                            "text": "",
                            },
                        "defaultConfiguration": {"level": severity},
                        "properties": {"tags": ["security"]},
                        }


                result = {
                        "ruleId": str(i),
                        # This appears in the line by line highlight on the individual issue view
                        "message": {"text": message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": str(fname)},
                                    "region": {"startLine": int(line)},
                                    }
                                }
                            ],
                        }
                results.append(result)
                i=i+1

          out = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "Betterscan", "informationUri": "https://betterscan.io", "semanticVersion": "0.9.9", "rules": list(rules.values())}},
                    "results": results,
                }
            ],
          }

          if output_sarif:
            with open('report.sarif', 'w') as f:
              json.dump(out, f)
         
          if output_html:
            print("Check your report in report.html file")

          print("Thank you for using Checkmate.")
