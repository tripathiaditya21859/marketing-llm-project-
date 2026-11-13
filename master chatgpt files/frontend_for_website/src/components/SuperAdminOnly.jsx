import {Navigate} from "react-router-dom";
import {useAuth} from "../context/AuthContext";
export default function SuperAdminOnly({children}){const {user}=useAuth();return user?.is_superadmin?children:<Navigate to="/" replace/>;}
