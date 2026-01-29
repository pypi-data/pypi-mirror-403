use hiargs::HiArgs;
use ignore::WalkState;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::{
    borrow::BorrowMut,
    ffi::{OsStr, OsString},
    sync::mpsc,
    thread,
};

mod haystack;
mod hiargs;
mod lowargs;
mod search;
#[macro_use]
mod messages;

#[pyclass]
pub struct PyArgs {
    pub patterns: Vec<String>,
    pub paths: Option<Vec<String>>,
    pub globs: Option<Vec<String>>,
    pub heading: Option<bool>,
    pub after_context: Option<u64>,
    pub before_context: Option<u64>,
    pub separator_field_context: Option<String>,
    pub separator_field_match: Option<String>,
    pub separator_context: Option<String>,
    pub sort: Option<PySortMode>,
    pub max_count: Option<u64>,
    pub line_number: Option<bool>,
    pub multiline: Option<bool>,
    pub case_sensitive: Option<bool>,
    pub smart_case: Option<bool>,
    pub no_ignore: Option<bool>,
    pub hidden: Option<bool>,
    pub json: Option<bool>,
    pub include_dirs: Option<bool>,
    pub max_depth: Option<usize>,
    pub absolute: Option<bool>,
    pub relative_to: Option<String>,
}

#[pymethods]
impl PyArgs {
    #[new]
    #[pyo3(signature = (
        patterns,
        paths=None,
        globs=None,
        heading=None,
        after_context=None,
        before_context=None,
        separator_field_context=None,
        separator_field_match=None,
        separator_context=None,
        sort=None,
        max_count=None,
        line_number=None,
        multiline=None,
        case_sensitive=None,
        smart_case=None,
        no_ignore=None,
        hidden=None,
        json=None,
        include_dirs=None,
        max_depth=None,
        absolute=None,
        relative_to=None,
    ))]
    fn new(
        patterns: Vec<String>,
        paths: Option<Vec<String>>,
        globs: Option<Vec<String>>,
        heading: Option<bool>,
        after_context: Option<u64>,
        before_context: Option<u64>,
        separator_field_context: Option<String>,
        separator_field_match: Option<String>,
        separator_context: Option<String>,
        sort: Option<PySortMode>,
        max_count: Option<u64>,
        line_number: Option<bool>,
        multiline: Option<bool>,
        case_sensitive: Option<bool>,
        smart_case: Option<bool>,
        no_ignore: Option<bool>,
        hidden: Option<bool>,
        json: Option<bool>,
        include_dirs: Option<bool>,
        max_depth: Option<usize>,
        absolute: Option<bool>,
        relative_to: Option<String>,
    ) -> Self {
        PyArgs {
            patterns,
            paths,
            globs,
            heading,
            after_context,
            before_context,
            separator_field_context,
            separator_field_match,
            separator_context,
            sort,
            max_count,
            line_number,
            multiline,
            case_sensitive,
            smart_case,
            no_ignore,
            hidden,
            json,
            include_dirs,
            max_depth,
            absolute,
            relative_to,
        }
    }
}

#[pyclass(eq)]
#[derive(PartialEq, Clone)]
#[pyo3(get_all)]
pub struct PySortMode {
    pub kind: PySortModeKind,
    pub reverse: bool,
}

#[pymethods]
impl PySortMode {
    #[new]
    #[pyo3(signature = (kind, reverse=false))]
    fn new(kind: PySortModeKind, reverse: bool) -> Self {
        PySortMode { kind, reverse }
    }
}

#[pyclass(eq)]
#[derive(PartialEq, Clone)]
#[pyo3(get_all)]
pub enum PySortModeKind {
    Path,
    LastModified,
    LastAccessed,
    Created,
}

fn build_patterns(patterns: Vec<String>) -> Vec<lowargs::PatternSource> {
    patterns
        .into_iter()
        .map(|pattern| lowargs::PatternSource::Regexp(pattern))
        .collect()
}

fn build_paths(paths: Vec<String>) -> Vec<OsString> {
    paths.into_iter().map(|path| OsString::from(path)).collect()
}

fn build_sort_mode_kind(kind: PySortModeKind) -> lowargs::SortModeKind {
    match kind {
        PySortModeKind::Path => lowargs::SortModeKind::Path,
        PySortModeKind::LastModified => lowargs::SortModeKind::LastModified,
        PySortModeKind::LastAccessed => lowargs::SortModeKind::LastAccessed,
        PySortModeKind::Created => lowargs::SortModeKind::Created,
    }
}

fn build_sort_mode(sort: Option<PySortMode>) -> Option<lowargs::SortMode> {
    if let Some(sort_mode) = sort {
        Some(lowargs::SortMode {
            kind: build_sort_mode_kind(sort_mode.kind),
            reverse: sort_mode.reverse,
        })
    } else {
        None
    }
}

fn build_context_mode(
    after_context: Option<u64>,
    before_context: Option<u64>,
) -> lowargs::ContextMode {
    let mut context_mode = lowargs::ContextMode::default();

    if let Some(after) = after_context {
        context_mode.set_after(after as usize);
    }

    if let Some(before) = before_context {
        context_mode.set_before(before as usize);
    }

    context_mode
}

fn pyargs_to_hiargs(py_args: &PyArgs, mode: lowargs::Mode) -> anyhow::Result<HiArgs> {
    let mut low_args = lowargs::LowArgs::default();

    low_args.patterns = build_patterns(py_args.patterns.clone());

    low_args.mode = mode;

    low_args.sort = build_sort_mode(py_args.sort.clone());

    low_args.heading = py_args.heading;

    low_args.max_count = py_args.max_count;

    low_args.line_number = py_args.line_number;

    low_args.context = build_context_mode(py_args.after_context, py_args.before_context);

    if let Some(globs) = &py_args.globs {
        low_args.globs = globs.clone();
    }

    if let Some(paths) = &py_args.paths {
        low_args.positional = build_paths(paths.clone());
    }

    if let Some(separator_field_context) = &py_args.separator_field_context {
        let sep = OsStr::new(separator_field_context);
        low_args.field_context_separator = lowargs::FieldContextSeparator::new(&sep).unwrap();
    }

    if let Some(separator_field_match) = &py_args.separator_field_match {
        let sep = OsStr::new(separator_field_match);
        low_args.field_match_separator = lowargs::FieldMatchSeparator::new(&sep).unwrap();
    }

    if let Some(separator_context) = &py_args.separator_context {
        let sep = OsStr::new(separator_context);
        low_args.context_separator = lowargs::ContextSeparator::new(&sep).unwrap();
    }

    if let Some(multiline) = py_args.multiline {
        low_args.multiline = multiline;
    }

    // Case sensitivity handling
    if let Some(true) = py_args.smart_case {
        low_args.case = lowargs::CaseMode::Smart;
    } else if let Some(false) = py_args.case_sensitive {
        low_args.case = lowargs::CaseMode::Insensitive;
    } else if let Some(true) = py_args.case_sensitive {
        low_args.case = lowargs::CaseMode::Sensitive;
    }

    // Ignore file handling
    if let Some(true) = py_args.no_ignore {
        low_args.no_ignore_dot = true;
        low_args.no_ignore_vcs = true;
        low_args.no_ignore_global = true;
        low_args.no_ignore_parent = true;
        low_args.no_ignore_files = true;
    }

    // Hidden files
    if let Some(hidden) = py_args.hidden {
        low_args.hidden = hidden;
    }

    // Include directories in results
    if let Some(include_dirs) = py_args.include_dirs {
        low_args.include_dirs = include_dirs;
    }

    // Max directory depth
    if let Some(max_depth) = py_args.max_depth {
        low_args.max_depth = Some(max_depth);
    }

    HiArgs::from_low_args(low_args)
}

#[pyfunction]
#[pyo3(name = "search")]
#[pyo3(signature = (
    patterns,
    paths=None,
    globs=None,
    heading=None,
    after_context=None,
    before_context=None,
    separator_field_context=None,
    separator_field_match=None,
    separator_context=None,
    sort=None,
    max_count=None,
    line_number=None,
    multiline=None,
    case_sensitive=None,
    smart_case=None,
    no_ignore=None,
    hidden=None,
    json=None,
))]
pub fn py_search(
    py: Python<'_>,
    patterns: Vec<String>,
    paths: Option<Vec<String>>,
    globs: Option<Vec<String>>,
    heading: Option<bool>,
    after_context: Option<u64>,
    before_context: Option<u64>,
    separator_field_context: Option<String>,
    separator_field_match: Option<String>,
    separator_context: Option<String>,
    sort: Option<PySortMode>,
    max_count: Option<u64>,
    line_number: Option<bool>,
    multiline: Option<bool>,
    case_sensitive: Option<bool>,
    smart_case: Option<bool>,
    no_ignore: Option<bool>,
    hidden: Option<bool>,
    json: Option<bool>,
) -> PyResult<Vec<String>> {
    py.detach(|| {
        let py_args = PyArgs {
            patterns,
            paths,
            globs,
            heading,
            after_context,
            before_context,
            separator_field_context,
            separator_field_match,
            separator_context,
            sort,
            max_count,
            line_number,
            multiline,
            case_sensitive,
            smart_case,
            no_ignore,
            hidden,
            json,
            include_dirs: None, // search doesn't use this
            max_depth: None,    // search doesn't use this
            absolute: None,     // search doesn't use this
            relative_to: None,  // search doesn't use this
        };

        let mode = if py_args.json == Some(true) {
            lowargs::Mode::Search(lowargs::SearchMode::JSON)
        } else {
            lowargs::Mode::default()
        };

        let args_result = pyargs_to_hiargs(&py_args, mode);

        if let Err(err) = args_result {
            return Err(PyValueError::new_err(err.to_string()));
        }

        let args = args_result.unwrap();

        let search_result = py_search_impl(&args);

        if let Err(err) = search_result {
            return Err(PyValueError::new_err(err.to_string()));
        }

        Ok(search_result.unwrap())
    })
}

fn py_search_impl(args: &HiArgs) -> anyhow::Result<Vec<String>> {
    // Check if JSON mode is requested
    if let lowargs::Mode::Search(lowargs::SearchMode::JSON) = args.mode() {
        return py_search_impl_json(args);
    }

    // Use parallel implementation when threads > 1 and no sorting requested
    if args.threads() > 1 && args.sort_mode().is_none() {
        return py_search_impl_parallel(args);
    }

    // Single-threaded implementation (also used when sorting is requested)
    let haystack_builder = args.haystack_builder();
    let unsorted = args
        .walk_builder()?
        .build()
        .filter_map(|result| haystack_builder.build_from_result(result));
    let haystacks = args.sort(unsorted);

    let args_matcher = args.matcher()?;
    let args_searcher = args.searcher()?;
    let args_printer = args.printer_no_color(vec![]);

    let mut results = Vec::new();

    let mut searcher = args.search_worker(args_matcher, args_searcher, args_printer)?;

    for haystack in haystacks {
        let search_result = match searcher.search(&haystack) {
            Ok(search_result) => search_result,
            // A broken pipe means graceful termination.
            Err(err) if err.kind() == std::io::ErrorKind::BrokenPipe => break,
            Err(err) => {
                err_message!("{}: {}", haystack.path().display(), err);
                continue;
            }
        };

        if search_result.has_match() {
            let printer = searcher.printer();
            let results_vec = printer.get_mut().borrow_mut();

            // Only include results for valid UTF-8 files
            match String::from_utf8(results_vec.get_ref().clone()) {
                Ok(results_str) => {
                    results.push(results_str);
                }
                Err(_) => {
                    // Skip this file as it contains invalid UTF-8 data
                    // (likely a binary file or file with a different encoding)
                }
            }

            let p = searcher.printer().borrow_mut();
            let p_inner = p.get_mut();
            p_inner.get_mut().clear();
        }
    }

    Ok(results)
}

/// Parallel search implementation
fn py_search_impl_parallel(args: &HiArgs) -> anyhow::Result<Vec<String>> {
    use std::sync::Mutex;

    let haystack_builder = args.haystack_builder();
    let results = Mutex::new(Vec::new());

    let searcher = args.search_worker(
        args.matcher()?,
        args.searcher()?,
        args.printer_no_color(vec![]),
    )?;

    args.walk_builder()?.build_parallel().run(|| {
        let haystack_builder = &haystack_builder;
        let results = &results;
        let mut searcher = searcher.clone();

        Box::new(move |result| {
            let haystack = match haystack_builder.build_from_result(result) {
                Some(haystack) => haystack,
                None => return WalkState::Continue,
            };

            // Clear the printer buffer for this file
            searcher.printer().get_mut().get_mut().clear();

            let search_result = match searcher.search(&haystack) {
                Ok(search_result) => search_result,
                Err(err) if err.kind() == std::io::ErrorKind::BrokenPipe => {
                    return WalkState::Quit;
                }
                Err(_) => {
                    return WalkState::Continue;
                }
            };

            if search_result.has_match() {
                let printer = searcher.printer();
                let results_vec = printer.get_mut();

                // Only include results for valid UTF-8 files
                if let Ok(results_str) = String::from_utf8(results_vec.get_ref().clone()) {
                    if let Ok(mut guard) = results.lock() {
                        guard.push(results_str);
                    }
                }
            }

            WalkState::Continue
        })
    });

    Ok(results.into_inner().unwrap())
}

/// JSON mode search implementation
fn py_search_impl_json(args: &HiArgs) -> anyhow::Result<Vec<String>> {
    use search::PatternMatcher;

    let haystack_builder = args.haystack_builder();
    let unsorted = args
        .walk_builder()?
        .build()
        .filter_map(|result| haystack_builder.build_from_result(result));
    let haystacks = args.sort(unsorted);

    let matcher = args.matcher()?;
    let mut searcher = args.searcher()?;

    let mut results = Vec::new();

    for haystack in haystacks {
        let mut printer_buf: Vec<u8> = vec![];

        let search_result = {
            let mut json_printer = args.printer_json(&mut printer_buf);
            let path = haystack.path();

            match &matcher {
                PatternMatcher::RustRegex(m) => {
                    let mut sink = json_printer.sink_with_path(m, path);
                    searcher.search_path(m, path, &mut sink)
                }
            }
        };

        match search_result {
            Ok(_) => {
                if !printer_buf.is_empty() {
                    if let Ok(s) = String::from_utf8(printer_buf) {
                        results.push(s);
                    }
                }
            }
            Err(err) if err.kind() == std::io::ErrorKind::BrokenPipe => break,
            Err(err) => {
                err_message!("{}: {}", haystack.path().display(), err);
                continue;
            }
        }
    }

    Ok(results)
}

#[pyfunction]
#[pyo3(name = "files")]
#[pyo3(signature = (
    patterns,
    paths=None,
    globs=None,
    heading=None,
    after_context=None,
    before_context=None,
    separator_field_context=None,
    separator_field_match=None,
    separator_context=None,
    sort=None,
    max_count=None,
    line_number=None,
    multiline=None,
    case_sensitive=None,
    smart_case=None,
    no_ignore=None,
    hidden=None,
    json=None,
    include_dirs=None,
    max_depth=None,
    absolute=None,
    relative_to=None,
))]
pub fn py_files(
    py: Python<'_>,
    patterns: Vec<String>,
    paths: Option<Vec<String>>,
    globs: Option<Vec<String>>,
    heading: Option<bool>,
    after_context: Option<u64>,
    before_context: Option<u64>,
    separator_field_context: Option<String>,
    separator_field_match: Option<String>,
    separator_context: Option<String>,
    sort: Option<PySortMode>,
    max_count: Option<u64>,
    line_number: Option<bool>,
    multiline: Option<bool>,
    case_sensitive: Option<bool>,
    smart_case: Option<bool>,
    no_ignore: Option<bool>,
    hidden: Option<bool>,
    json: Option<bool>,
    include_dirs: Option<bool>,
    max_depth: Option<usize>,
    absolute: Option<bool>,
    relative_to: Option<String>,
) -> PyResult<Vec<String>> {
    py.detach(|| {
        let py_args = PyArgs {
            patterns,
            paths,
            globs,
            heading,
            after_context,
            before_context,
            separator_field_context,
            separator_field_match,
            separator_context,
            sort,
            max_count,
            line_number,
            multiline,
            case_sensitive,
            smart_case,
            no_ignore,
            hidden,
            json,
            include_dirs,
            max_depth,
            absolute,
            relative_to,
        };

        let args_result = pyargs_to_hiargs(&py_args, lowargs::Mode::Files);

        if let Err(err) = args_result {
            return Err(PyValueError::new_err(err.to_string()));
        }

        let args = args_result.unwrap();

        let files_result = py_files_impl(
            &args,
            py_args.absolute.unwrap_or(false),
            py_args.relative_to.as_deref(),
        );

        if let Err(err) = files_result {
            return Err(PyValueError::new_err(err.to_string()));
        }

        Ok(files_result.unwrap())
    })
}

fn py_files_impl(
    args: &HiArgs,
    absolute: bool,
    relative_to: Option<&str>,
) -> anyhow::Result<Vec<String>> {
    // Use parallel implementation when threads > 1 and no sorting requested
    if args.threads() > 1 && args.sort_mode().is_none() {
        return py_files_impl_parallel(args, absolute, relative_to);
    }

    // Get cwd once if needed for making paths absolute
    let cwd = if absolute {
        std::env::current_dir().ok()
    } else {
        None
    };

    // Prepare prefix for relative path stripping
    let prefix = relative_to.map(|p| {
        let mut s = p.to_string();
        if !s.ends_with('/') && !s.ends_with('\\') {
            s.push('/');
        }
        s
    });

    // Single-threaded implementation (also used when sorting is requested)
    let haystack_builder = args.haystack_builder();
    let walk_builder = args.walk_builder()?;

    let unsorted = walk_builder
        .build()
        .filter_map(|result| haystack_builder.build_from_result(result));

    let haystacks = args.sort(unsorted);

    let mut matches = Vec::new();

    for haystack in haystacks {
        if args.quit_after_match() {
            break;
        }

        if let Some(max_count) = args.max_count() {
            if matches.len() >= max_count as usize {
                break;
            }
        }

        let path = haystack.path();
        let mut path_str = if let Some(ref cwd) = cwd {
            if !path.is_absolute() {
                cwd.join(path).to_str().map(|s| s.to_string())
            } else {
                path.to_str().map(|s| s.to_string())
            }
        } else {
            path.to_str().map(|s| s.to_string())
        };

        // Strip prefix if relative_to is set
        if let (Some(ref mut p), Some(ref pfx)) = (&mut path_str, &prefix) {
            if p.starts_with(pfx) {
                *p = p[pfx.len()..].to_string();
            }
        }

        if let Some(p) = path_str {
            matches.push(p);
        }
    }

    Ok(matches)
}

/// Parallel file listing implementation
fn py_files_impl_parallel(
    args: &HiArgs,
    absolute: bool,
    relative_to: Option<&str>,
) -> anyhow::Result<Vec<String>> {
    let haystack_builder = args.haystack_builder();
    let max_count = args.max_count();
    let quit_after_match = args.quit_after_match();

    // Get cwd once if needed for making paths absolute
    let cwd = if absolute {
        std::env::current_dir().ok()
    } else {
        None
    };

    // Prepare prefix for relative path stripping
    let prefix: Option<String> = relative_to.map(|p| {
        let mut s = p.to_string();
        if !s.ends_with('/') && !s.ends_with('\\') {
            s.push('/');
        }
        s
    });

    let (tx, rx) = mpsc::channel::<String>();

    // Spawn collector thread
    let collector = thread::spawn(move || -> Vec<String> {
        let mut results = Vec::new();
        for path in rx.iter() {
            results.push(path);
            if quit_after_match {
                break;
            }
            if let Some(max) = max_count {
                if results.len() >= max as usize {
                    break;
                }
            }
        }
        results
    });

    // Parallel directory walk
    args.walk_builder()?.build_parallel().run(|| {
        let haystack_builder = &haystack_builder;
        let tx = tx.clone();
        let cwd = &cwd;
        let prefix = &prefix;

        Box::new(move |result| {
            let haystack = match haystack_builder.build_from_result(result) {
                Some(haystack) => haystack,
                None => return WalkState::Continue,
            };

            let path = haystack.path();
            let mut path_str = if let Some(ref cwd) = cwd {
                if !path.is_absolute() {
                    cwd.join(path).to_str().map(|s| s.to_string())
                } else {
                    path.to_str().map(|s| s.to_string())
                }
            } else {
                path.to_str().map(|s| s.to_string())
            };

            // Strip prefix if relative_to is set
            if let (Some(ref mut p), Some(ref pfx)) = (&mut path_str, prefix) {
                if p.starts_with(pfx) {
                    *p = p[pfx.len()..].to_string();
                }
            }

            if let Some(p) = path_str {
                match tx.send(p) {
                    Ok(_) => WalkState::Continue,
                    Err(_) => WalkState::Quit,
                }
            } else {
                WalkState::Continue
            }
        })
    });

    // Drop the original sender so collector thread can finish
    drop(tx);

    // Collect results
    Ok(collector.join().unwrap())
}
