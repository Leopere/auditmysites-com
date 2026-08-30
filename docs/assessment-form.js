(function () {
  'use strict';

  const proofUrl = 'https://forms.motherboardrepair.ca/api/form-proof';
  const submitUrl = 'https://forms.motherboardrepair.ca/api/submit';
  const formId = 'auditmysites_assessment';
  const maxCounter = 10000000;
  let cachedChallenge = null;
  const form = document.getElementById('assessment-form');
  const status = document.getElementById('form-status');
  const button = document.getElementById('submit-request');
  if (!form || !status || !button) return;
  button.disabled = false;

  function base64Url(bytes) {
    let binary = '';
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function leadingZeroBits(bytes) {
    let count = 0;
    for (const byte of bytes) {
      if (byte === 0) { count += 8; continue; }
      for (let bit = 7; bit >= 0 && (byte & (1 << bit)) === 0; bit -= 1) count += 1;
      break;
    }
    return count;
  }

  function proofBinding(payload) {
    return JSON.stringify(['mrc-form-proof-v1', payload.form_id || payload.source || '', payload.name || '', payload.email || '', payload.phone || payload.phone_number || '', payload.company || '', payload.message || payload.notes || '', payload.slack_profile || '']);
  }

  async function challenge() {
    if (cachedChallenge && cachedChallenge.expires_at > Date.now() + 60000) return cachedChallenge;
    const response = await fetch(proofUrl, { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Could not prepare the protected form.');
    cachedChallenge = await response.json();
    return cachedChallenge;
  }

  async function solve(payload) {
    const item = await challenge();
    const delay = Math.max(0, Number(item.ready_at) - Date.now());
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    const encoder = new TextEncoder();
    const bindingHash = base64Url(new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(proofBinding(payload)))));
    for (let counter = 0; counter <= maxCounter; counter += 1) {
      const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(`${item.challenge}.${bindingHash}.${counter}`)));
      if (leadingZeroBits(digest) >= Number(item.difficulty)) return { form_proof_token: item.challenge, form_proof_counter: counter };
    }
    throw new Error('Could not prepare the protected form.');
  }

  function payloadFromForm() {
    const data = new FormData(form);
    const siteUrl = String(data.get('site_url') || '').trim();
    const market = String(data.get('market') || '').trim();
    const goals = String(data.get('message') || '').trim();
    return {
      form_id: formId,
      name: String(data.get('name') || '').trim(),
      email: String(data.get('email') || '').trim(),
      phone: String(data.get('phone') || '').trim(),
      company: siteUrl,
      message: `Website: ${siteUrl}\nMarket: ${market || 'Not specified'}\n\nAssessment goals:\n${goals}`,
      extra_fields: { website_url: siteUrl, target_market: market, source_url: window.location.origin + window.location.pathname },
    };
  }

  async function send(payload, retry = true) {
    const response = await fetch(submitUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ ...payload, ...await solve(payload) }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 403 && result.code === 'FORM_PROOF_INVALID' && retry) {
      cachedChallenge = null;
      return send(payload, false);
    }
    if (!response.ok || result.ok !== true || result.success !== true) throw new Error(result.error || result.message || 'We could not send your request. Please try again.');
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (form.elements.website.value) {
      form.reset();
      status.textContent = 'Thanks. Your request has been received.';
      return;
    }
    button.disabled = true;
    status.textContent = 'Preparing secure submission…';
    try {
      await send(payloadFromForm());
      form.reset();
      status.textContent = 'Thanks. Your assessment request has been sent.';
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : 'We could not send your request. Please try again.';
    } finally {
      button.disabled = false;
    }
  });
}());
