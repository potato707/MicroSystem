/**
 * ComplaintDetailsPage Component
 * 
 * Example implementation showing how to integrate the CommentForm component
 * into a complaint details page with proper state management
 */

import React, { useState, useEffect } from 'react';
import CommentForm from '../components/CommentForm';
import './ComplaintDetailsPage.css';

const ComplaintDetailsPage = ({ complaintId }) => {
  const [complaint, setComplaint] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshComments, setRefreshComments] = useState(0);
  
  // Get auth token (implement according to your auth system)
  const authToken = localStorage.getItem('authToken'); // or useAuth hook, etc.

  // Fetch complaint details and comments
  useEffect(() => {
    const fetchComplaintData = async () => {
      try {
        const response = await fetch(`/hr/client-complaints/${complaintId}/`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setComplaint(data);
          setComments(data.comments || []);
        }
      } catch (error) {
        console.error('Error fetching complaint:', error);
      } finally {
        setLoading(false);
      }
    };

    if (complaintId && authToken) {
      fetchComplaintData();
    }
  }, [complaintId, authToken, refreshComments]);

  // Handle new comment added
  const handleCommentAdded = (newComment) => {
    // Add the new comment to the list (it will appear at the top due to backend sorting)
    setComments(prevComments => [newComment, ...prevComments]);
    
    // Optional: Show success notification
    showNotification(`Comment added successfully (${newComment.is_internal ? 'Internal' : 'Public'})`);
    
    // Optional: Refresh comments from server to ensure consistency
    // setRefreshComments(prev => prev + 1);
  };

  const showNotification = (message) => {
    // Implement your notification system here
    console.log(message);
  };

  if (loading) {
    return <div className="loading">Loading complaint details...</div>;
  }

  if (!complaint) {
    return <div className="error">Complaint not found</div>;
  }

  return (
    <div className="complaint-details-page">
      {/* Complaint Header */}
      <div className="complaint-header">
        <h1>{complaint.title}</h1>
        <div className="complaint-meta">
          <span className={`status-badge ${complaint.status}`}>
            {/* Use display_status_combined for better UX - shows automated communication status */}
            {complaint.display_status_combined || complaint.status_display}
          </span>
          <span className="priority">Priority: {complaint.priority_display}</span>
          <span className="client-info">
            Client: {complaint.client_name} ({complaint.client_email})
          </span>
        </div>
      </div>

      {/* Complaint Description */}
      <div className="complaint-content">
        <h2>Description</h2>
        <p>{complaint.description}</p>
      </div>

      {/* Comments Section */}
      <div className="comments-section">
        <h2>Comments & Communication</h2>
        
        {/* Add Comment Form */}
        <div className="add-comment-section">
          <h3>Add New Comment</h3>
          <CommentForm
            complaintId={complaintId}
            authToken={authToken}
            onCommentAdded={handleCommentAdded}
            isLoading={loading}
          />
        </div>

        {/* Comments List */}
        <div className="comments-list">
          <h3>All Comments ({comments.length})</h3>
          {comments.length === 0 ? (
            <div className="no-comments">
              <p>No comments yet. Be the first to add a comment!</p>
            </div>
          ) : (
            <div className="comments-container">
              {comments.map((comment) => (
                <CommentItem 
                  key={comment.id} 
                  comment={comment} 
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Individual Comment Component
const CommentItem = ({ comment }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className={`comment-item ${comment.is_internal ? 'internal-comment' : 'public-comment'}`}>
      <div className="comment-header">
        <div className="author-info">
          <strong>{comment.author_name}</strong>
          <span className="comment-date">{formatDate(comment.created_at)}</span>
        </div>
        <div className="comment-type">
          {comment.is_internal ? (
            <span className="internal-badge">
              🔒 Internal
            </span>
          ) : (
            <span className="public-badge">
              👁️ Public
            </span>
          )}
        </div>
      </div>
      <div className="comment-content">
        {comment.comment}
      </div>
    </div>
  );
};

export default ComplaintDetailsPage;