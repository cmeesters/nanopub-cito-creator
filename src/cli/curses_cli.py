import curses
import logging
from nanopub import NanopubConf, load_profile
from services.crossref_service import get_cited_papers
from services.nanopub_service import create_nanopub
from models.citation_types import CITATION_TYPES, CONFLICTING_COMBINATIONS

def run_curses(app_state):
    """Entry point for curses mode. Returns exit code."""
    return curses.wrapper(_curses_main, app_state)

def _curses_main(stdscr, app_state):
    curses.curs_set(1)
    stdscr.clear()

    # Input DOI if not supplied
    if app_state.initial_doi:
        doi = app_state.initial_doi.strip()
    else:
        doi = _prompt(stdscr, "Enter DOI: ")
    if not doi:
        _message(stdscr, "No DOI provided. Press any key to exit.")
        stdscr.getch()
        return 1

    app_state.reset()
    app_state.set_doi(doi)

    _message(stdscr, f"Fetching references for DOI: {doi} ...")
    cited = get_cited_papers(doi)
    if not cited:
        _message(stdscr, "No cited papers found. Press any key to exit.")
        stdscr.getch()
        return 0

    app_state.set_cited_papers(cited)

    # Iterate cited papers and select CiTO types
    for cited_doi, title in cited.items():
        choices = list(CITATION_TYPES.keys())
        selected = _checklist_dialog(
            stdscr,
            title=f"Select CiTO types for:\n{title}\nDOI: {cited_doi}",
            choices=choices,
        )
        if selected is None:  # user pressed q to skip further processing
            break
        if selected:
            # Conflict check
            if _has_conflicts(selected):
                proceed = _yes_no(stdscr, "Conflicting CiTO types selected. Proceed?")
                if not proceed:
                    continue
            app_state.add_citation(cited_doi, selected)

    citations = app_state.get_citations()
    if not citations:
        _message(stdscr, "No selections made. Press any key to exit.")
        stdscr.getch()
        return 0

    # Confirm publication (unless auto_publish)
    if not app_state.auto_publish:
        if not _yes_no(stdscr, f"Publish nanopub with {len(citations)} citation(s)?"):
            _message(stdscr, "Publication cancelled. Press any key to exit.")
            stdscr.getch()
            return 0

    # Create nanopub
    conf = NanopubConf(
        use_test_server=app_state.use_test_server,
        profile=load_profile(),
        add_prov_generated_time=True,
        attribute_publication_to_profile=True,
    )
    _message(stdscr, "Publishing nanopub...")
    try:
        uri = create_nanopub(doi, citations, conf)
        _message(stdscr, f"Nanopub published:\n{uri}\n\nPress any key to exit.")
        stdscr.getch()
        return 0
    except Exception as e:
        logging.exception("Nanopub creation failed")
        _message(stdscr, f"Failed to publish nanopub:\n{e}\n\nPress any key to exit.")
        stdscr.getch()
        return 1

def _prompt(stdscr, prompt):
    stdscr.clear()
    stdscr.addstr(0, 0, prompt)
    stdscr.refresh()
    curses.echo()
    s = stdscr.getstr(0, len(prompt), 256)
    curses.noecho()
    try:
        return s.decode("utf-8").strip()
    except Exception:
        return str(s).strip()

def _message(stdscr, text):
    stdscr.clear()
    stdscr.addstr(0, 0, text)
    stdscr.refresh()

def _yes_no(stdscr, question):
    stdscr.clear()
    stdscr.addstr(0, 0, question)
    stdscr.addstr(2, 0, "[y] Yes    [n] No")
    stdscr.refresh()
    while True:
        ch = stdscr.getch()
        if ch in (ord('y'), ord('Y')):
            return True
        if ch in (ord('n'), ord('N')):
            return False

def _has_conflicts(selected_keys):
    for a, b in CONFLICTING_COMBINATIONS:
        if a in selected_keys and b in selected_keys:
            return True
    return False

def _checklist_dialog(stdscr, title, choices):
    """
    Simple checklist:
    - Up/Down to navigate
    - Space to toggle
    - Enter to confirm
    - q to stop processing
    Returns list of selected labels, or None to stop processing.
    """
    selected = set()
    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, title)
        stdscr.addstr(2, 0, "Use Up/Down to navigate, Space to toggle, Enter to confirm, q to stop.")
        # Render list
        for i, label in enumerate(choices):
            mark = "[x]" if label in selected else "[ ]"
            prefix = ">> " if i == idx else "   "
            stdscr.addstr(4 + i, 0, f"{prefix}{mark} {label}")
        stdscr.refresh()

        ch = stdscr.getch()
        if ch in (curses.KEY_UP, ord('k')):
            if idx > 0:
                idx -= 1
        elif ch in (curses.KEY_DOWN, ord('j')):
            if idx < len(choices) - 1:
                idx += 1
        elif ch == ord(' '):
            label = choices[idx]
            if label in selected:
                selected.remove(label)
            else:
                selected.add(label)
        elif ch in (curses.KEY_ENTER, 10, 13):
            return list(selected)
        elif ch in (ord('q'), ord('Q')):
            return None