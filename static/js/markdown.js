(function (root) {
  'use strict';

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (character) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }[character];
    });
  }

  function renderInline(value) {
    var code = [];
    var safe = escapeHtml(value).replace(/`([^`\n]+)`/g, function (_, content) {
      code.push('<code>' + content + '</code>');
      return '\u0000CODE' + (code.length - 1) + '\u0000';
    });

    safe = safe
      .replace(/\*\*([^*\n][\s\S]*?)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');

    return safe.replace(/\u0000CODE(\d+)\u0000/g, function (_, index) {
      return code[Number(index)];
    });
  }

  function render(markdown) {
    var lines = String(markdown == null ? '' : markdown)
      .replace(/\r\n?/g, '\n')
      .split('\n');
    var html = [];
    var paragraph = [];
    var listType = null;
    var codeLines = [];
    var inCode = false;

    function flushParagraph() {
      if (!paragraph.length) return;
      html.push('<p>' + paragraph.map(renderInline).join('<br>') + '</p>');
      paragraph = [];
    }

    function closeList() {
      if (!listType) return;
      html.push('</' + listType + '>');
      listType = null;
    }

    function openList(type) {
      if (listType === type) return;
      closeList();
      html.push('<' + type + '>');
      listType = type;
    }

    lines.forEach(function (line) {
      var trimmed = line.trim();

      if (/^```/.test(trimmed)) {
        flushParagraph();
        closeList();
        if (inCode) {
          html.push('<pre><code>' + escapeHtml(codeLines.join('\n')) + '</code></pre>');
          codeLines = [];
        }
        inCode = !inCode;
        return;
      }

      if (inCode) {
        codeLines.push(line);
        return;
      }

      if (!trimmed) {
        flushParagraph();
        closeList();
        return;
      }

      var unordered = trimmed.match(/^[-+*]\s+(.+)$/);
      if (unordered) {
        flushParagraph();
        openList('ul');
        html.push('<li>' + renderInline(unordered[1]) + '</li>');
        return;
      }

      var ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
      if (ordered) {
        flushParagraph();
        openList('ol');
        html.push('<li>' + renderInline(ordered[1]) + '</li>');
        return;
      }

      var heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        flushParagraph();
        closeList();
        var level = Math.min(heading[1].length + 3, 6);
        html.push('<h' + level + '>' + renderInline(heading[2]) + '</h' + level + '>');
        return;
      }

      var quote = trimmed.match(/^>\s?(.+)$/);
      if (quote) {
        flushParagraph();
        closeList();
        html.push('<blockquote>' + renderInline(quote[1]) + '</blockquote>');
        return;
      }

      closeList();
      paragraph.push(trimmed);
    });

    if (inCode) {
      codeLines.unshift('```');
      paragraph.push(codeLines.join('\n'));
    }
    flushParagraph();
    closeList();
    return html.join('');
  }

  var api = {
    escape: escapeHtml,
    render: render,
    renderPlain: function (value) {
      return escapeHtml(value).replace(/\r\n?|\n/g, '<br>');
    }
  };

  root.BBMarkdown = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
