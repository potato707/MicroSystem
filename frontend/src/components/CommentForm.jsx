/**
 * CommentForm Component
 * 
 * A React component for adding comments to complaints with internal/public toggle
 * 
 * Features:
 * - Text area for comment input
 * - Checkbox to toggle between internal (company-only) and public (client-visible) comments
 * - Visual indicators for comment visibility
 * - Proper API integration with the backend
 */

import React, { useState } from 'react';
import './CommentForm.css';

const CommentForm = ({ 
  complaintId, 
  authToken, 
  onCommentAdded, 
  isLoading = false 
}) => {
  const [comment, setComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!comment.trim()) {
      setError('Comment cannot be empty');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/hr/client-complaints/${complaintId}/comments/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comment: comment.trim(),
          is_internal: isInternal
        })
      });

      if (response.ok) {
        const newComment = await response.json();
        
        // Reset form
        setComment('');
        setIsInternal(false);
        
        // Notify parent component
        if (onCommentAdded) {
          onCommentAdded(newComment);
        }
        
        console.log(`Comment added successfully: ${isInternal ? 'Internal' : 'Public'}`);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to add comment');
      }
    } catch (err) {
      console.error('Error adding comment:', err);
      setError(err.message || 'Failed to add comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleVisibility = (checked) => {
    setIsInternal(checked);
  };

  return (
    <div className="comment-form">
      <form onSubmit={handleSubmit}>
        <div className="comment-input-section">
          <label htmlFor="comment-textarea" className="comment-label">
            Add Comment
          </label>
          <textarea
            id="comment-textarea"
            className={`comment-textarea ${isInternal ? 'internal-comment' : 'public-comment'}`}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={
              isInternal 
                ? "Add an internal comment (company only)..." 
                : "Add a comment (visible to client)..."
            }
            rows={4}
            disabled={submitting || isLoading}
            required
          />
          
          {/* Character counter */}
          <div className="character-counter">
            {comment.length} characters
          </div>
        </div>

        {/* Visibility Toggle Section */}
        <div className="visibility-toggle-section">
          <div className="toggle-container">
            <label className="toggle-label">
              <input
                type="checkbox"
                className="visibility-checkbox"
                checked={isInternal}
                onChange={(e) => handleToggleVisibility(e.target.checked)}
                disabled={submitting || isLoading}
              />
              <span className="checkmark"></span>
              <span className="toggle-text">
                Internal Comment (Company Only)
              </span>
            </label>
          </div>
          
          {/* Visibility Indicator */}
          <div className={`visibility-indicator ${isInternal ? 'internal' : 'public'}`}>
            <div className="indicator-icon">
              {isInternal ? '🔒' : '👁️'}
            </div>
            <div className="indicator-text">
              <strong>
                {isInternal ? 'Internal Comment' : 'Public Comment'}
              </strong>
              <br />
              <small>
                {isInternal 
                  ? 'Only visible to company staff members'
                  : 'Visible to client and company staff'
                }
              </small>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className={`submit-button ${isInternal ? 'internal-btn' : 'public-btn'}`}
            disabled={submitting || isLoading || !comment.trim()}
          >
            {submitting ? (
              <>
                <span className="spinner"></span>
                Adding Comment...
              </>
            ) : (
              <>
                {isInternal ? '🔒 Add Internal Comment' : '📢 Add Public Comment'}
              </>
            )}
          </button>
          
          {comment.trim() && (
            <button
              type="button"
              className="clear-button"
              onClick={() => {
                setComment('');
                setError(null);
              }}
              disabled={submitting || isLoading}
            >
              Clear
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default CommentForm;